"""End-to-end test: cross-chain contract regulation via AuditProxy.

Reuses the system-predeployed ``core.AuditProxy``, deploys PREDA audit
implementations (KycAudit, CftAudit) that import ``core.AuditInterface``
directly, and GCL cross-chain
contracts (CrossTransfer, AppContract), then verifies that AuditProxy correctly
regulates function calls on real user-deployed contracts.

Test matrix:
  - IT-CC1: KYC audit on AppContract
  - IT-CC2: CFT audit on CrossTransfer
  - IT-CC3: Unbind restores normal operation
  - IT-CC4: Cross-contract binding isolation
"""

import hashlib
import os
import uuid
import time

import krock32
import pytest

from dioxide_python_sdk.client.dioxclient import DioxClient, DioxError
from dioxide_python_sdk.client.account import DioxAccount

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTRACTS_DIR = os.path.join(BASE_DIR, "contracts")
CROSSCHAIN_DIR = os.path.join(CONTRACTS_DIR, "crosschain")
REG_CONTRACTS_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "..", "oxd_bc", "rvm_contracts")
)
CORE_AUDIT_DAPP = "core"

_SUFFIX = uuid.uuid4().hex[:4]
AUDIT_DAPP = f"RA{_SUFFIX}"
CC_DAPP = f"CC{_SUFFIX}"

REGULATOR_KEY_B64 = "6NHi+B1jWQ3gDfC2GFHHBoNPEhCWa9lkIUMGRtRc2LbYtNrHang1QL/XdXt0pSAVw0v4cX7iDz55Ksnf41cIfA=="

DUMMY_DOMAIN = [100, 105, 111, 120, 48, 49]
DUMMY_RECEIVER = [1, 2, 3, 4]
DUMMY_MESSAGE = [72, 101, 108, 108, 111]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _preda_hash(name: str) -> str:
    """SHA-256 hash of a name string, encoded as Crockford Base32 lowercase
    to match the PREDA `hash` type wire format."""
    digest = hashlib.sha256(name.encode()).digest()
    encoder = krock32.Encoder()
    encoder.update(digest)
    return encoder.finalize().lower()

def _send_tx(client, user, function, args, timeout=60):
    """Send a transaction, wait for confirmation, return (tx_hash, success).

    If the RPC rejects the transaction outright (e.g. mempool regulation),
    returns (None, False).
    """
    try:
        tx_hash = client.send_transaction(
            user=user, function=function, args=args,
            is_sync=True, timeout=timeout,
        )
    except DioxError:
        return None, False
    except Exception:
        return None, False
    tx = client.get_transaction(tx_hash)
    ok = client.is_tx_success(tx)
    if not ok:
        relays = client.get_all_relay_transactions(tx, detail=True)
        for r in relays:
            if hasattr(r, "Invocation") and r.Invocation.Status != "IVKRET_SUCCESS":
                return tx_hash, False
    return tx_hash, ok


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    rpc_url = os.environ.get("DIOX_RPC_URL", "http://127.0.0.1:45678/api")
    ws_url = os.environ.get("DIOX_WS_URL", rpc_url.replace("http", "ws", 1))
    return DioxClient(url=rpc_url, ws_url=ws_url)


@pytest.fixture(scope="module")
def deployer(client):
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def regulator(client):
    acc = DioxAccount.from_key(REGULATOR_KEY_B64)
    assert acc is not None, "Failed to load regulator key"
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def user_approved(client):
    """KYC-approved, NOT CFT-sanctioned."""
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def user_blocked(client):
    """NOT KYC-approved, CFT-sanctioned."""
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def user_cft_kyc(client):
    """KYC-approved AND CFT-sanctioned (for isolation test IT-CC4)."""
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def user_plain(client):
    """NOT KYC-approved, NOT CFT-sanctioned (for isolation test IT-CC4)."""
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def audit_dapp(client, deployer):
    """Deploy audit implementations and reuse the predeployed core AuditProxy."""
    _, ok = client.create_dapp(deployer, AUDIT_DAPP, 10**12)
    assert ok, f"Failed to create audit dapp {AUDIT_DAPP}"

    contracts = {
        os.path.join(REG_CONTRACTS_DIR, "kyc_audit.prd"): None,
        os.path.join(REG_CONTRACTS_DIR, "cft_audit.prd"): None,
    }
    tx = client.deploy_contracts(AUDIT_DAPP, deployer, contracts, compile_time=20)
    assert tx is not None, "Audit contracts deploy failed"

    proxy_info = client.get_contract_info(CORE_AUDIT_DAPP, "AuditProxy")
    kyc_info = client.get_contract_info(AUDIT_DAPP, "KycAudit")
    cft_info = client.get_contract_info(AUDIT_DAPP, "CftAudit")
    regulation_state = client.get_regulation_state()
    assert int(regulation_state.State.AuditContractIdRaw) == int(proxy_info.ContractID)

    return {
        "proxy_cid": proxy_info.ContractID,
        "proxy_cvid": proxy_info.ContractVersionID,
        "kyc_cvid": kyc_info.ContractVersionID,
        "cft_cvid": cft_info.ContractVersionID,
    }


@pytest.fixture(scope="module")
def cc_dapp(client, deployer):
    """Deploy cross-chain DApp with all GCL contracts and set up SDP bindings."""
    _, ok = client.create_dapp(deployer, CC_DAPP, 10**12)
    assert ok, f"Failed to create crosschain dapp {CC_DAPP}"

    iface_dir = os.path.join(CROSSCHAIN_DIR, "interfaces")
    lib_dir = os.path.join(CROSSCHAIN_DIR, "lib")

    contracts = {
        os.path.join(iface_dir, "IAuthMessage.gcl"): None,
        os.path.join(iface_dir, "IContractUsingSDP.gcl"): None,
        os.path.join(iface_dir, "ISDPMessage.gcl"): None,
        os.path.join(iface_dir, "ISubProtocol.gcl"): None,
        os.path.join(lib_dir, "am", "AMLib.gcl"): None,
        os.path.join(lib_dir, "sdp", "SDPLib.gcl"): None,
        os.path.join(lib_dir, "utils", "BytesToTypes.gcl"): None,
        os.path.join(lib_dir, "utils", "SizeOf.gcl"): None,
        os.path.join(lib_dir, "utils", "TLVUtils.gcl"): None,
        os.path.join(lib_dir, "utils", "TypesToBytes.gcl"): None,
        os.path.join(lib_dir, "utils", "Utils.gcl"): None,
        os.path.join(CROSSCHAIN_DIR, "AuthMsg.gcl"): {
            "_owner": deployer.address, "_relayer": deployer.address,
        },
        os.path.join(CROSSCHAIN_DIR, "SDPMsg.gcl"): {"_owner": deployer.address},
        os.path.join(CROSSCHAIN_DIR, "CrossTransfer.gcl"): {"_owner": deployer.address},
        os.path.join(CROSSCHAIN_DIR, "AppContract.gcl"): {"_owner": deployer.address},
    }
    tx = client.deploy_contracts(CC_DAPP, deployer, contracts, compile_time=30)
    assert tx is not None, "Cross-chain contracts deploy failed"

    am_info = client.get_contract_info(CC_DAPP, "AuthMsg")
    sdp_info = client.get_contract_info(CC_DAPP, "SDPMsg")
    ct_info = client.get_contract_info(CC_DAPP, "CrossTransfer")
    app_info = client.get_contract_info(CC_DAPP, "AppContract")

    am_cvid = am_info.ContractVersionID
    sdp_cvid = sdp_info.ContractVersionID
    sdp_addr = f"0x{sdp_cvid:016X}:contract"
    am_addr = f"0x{am_cvid:016X}:contract"

    client.send_transaction(
        deployer, f"{CC_DAPP}.SDPMsg.setAmContract",
        {"_amContractId": am_cvid, "_amAddress": am_addr}, is_sync=True)
    client.send_transaction(
        deployer, f"{CC_DAPP}.SDPMsg.setLocalDomain",
        {"domain": DUMMY_DOMAIN}, is_sync=True)
    client.send_transaction(
        deployer, f"{CC_DAPP}.AuthMsg.setProtocol",
        {"protocolID": sdp_cvid, "protocolAddress": sdp_addr, "protocolType": 0},
        is_sync=True)
    client.send_transaction(
        deployer, f"{CC_DAPP}.CrossTransfer.setProtocol",
        {"_protocolContractId": sdp_cvid, "_protocolAddress": sdp_addr},
        is_sync=True)
    client.send_transaction(
        deployer, f"{CC_DAPP}.AppContract.setProtocol",
        {"_protocolContractId": sdp_cvid, "_protocolAddress": sdp_addr},
        is_sync=True)

    return {
        "ct_cid": ct_info.ContractID,
        "ct_cvid": ct_info.ContractVersionID,
        "app_cid": app_info.ContractID,
        "app_cvid": app_info.ContractVersionID,
    }


@pytest.fixture(scope="module")
def env(client, deployer, regulator,
        user_approved, user_blocked, user_cft_kyc, user_plain,
        audit_dapp, cc_dapp):
    """Wire up regulation: register, bind, approve and sanction."""
    proxy_cid = audit_dapp["proxy_cid"]
    kyc_cvid = audit_dapp["kyc_cvid"]
    cft_cvid = audit_dapp["cft_cvid"]
    ct_bind_id = cc_dapp["ct_cid"]
    app_bind_id = cc_dapp["app_cid"]

    regulation_state = client.get_regulation_state()
    assert int(regulation_state.State.AuditContractIdRaw) == int(proxy_cid)

    kyc_hash = _preda_hash("kyc")
    cft_hash = _preda_hash("cft")

    def _assert_relay_success(tx_hash, label):
        tx_detail = client.get_transaction(tx_hash)
        assert client.is_tx_success(tx_detail), f"{label}: initial tx failed"
        relays = client.get_all_relay_transactions(tx_detail, detail=True)
        if relays:
            for r in relays:
                assert r.Invocation.Status == "IVKRET_SUCCESS", \
                    f"{label} relay failed: {r.Invocation.Status}"

    tx = client.audit_proxy_register(CORE_AUDIT_DAPP, regulator, kyc_hash, kyc_cvid, sync=True)
    assert tx is not None, "audit_proxy_register kyc tx returned None"
    _assert_relay_success(tx, "register(kyc)")

    tx = client.audit_proxy_register(CORE_AUDIT_DAPP, regulator, cft_hash, cft_cvid, sync=True)
    assert tx is not None, "audit_proxy_register cft tx returned None"
    _assert_relay_success(tx, "register(cft)")

    tx = client.audit_proxy_bind(CORE_AUDIT_DAPP, regulator, ct_bind_id, cft_hash, sync=True)
    assert tx is not None, "audit_proxy_bind cft->ct tx returned None"
    _assert_relay_success(tx, "bind(cft->ct)")

    tx = client.audit_proxy_bind(CORE_AUDIT_DAPP, regulator, app_bind_id, kyc_hash, sync=True)
    assert tx is not None, "audit_proxy_bind kyc->app tx returned None"
    _assert_relay_success(tx, "bind(kyc->app)")

    tx = client.send_transaction(
        deployer, f"{AUDIT_DAPP}.KycAudit.approve",
        {"addr": user_approved.address}, is_sync=True)
    _assert_relay_success(tx, "kyc.approve(user_approved)")

    tx = client.send_transaction(
        deployer, f"{AUDIT_DAPP}.KycAudit.approve",
        {"addr": user_cft_kyc.address}, is_sync=True)
    _assert_relay_success(tx, "kyc.approve(user_cft_kyc)")

    tx = client.send_transaction(
        deployer, f"{AUDIT_DAPP}.CftAudit.add_sanction",
        {"addr": user_blocked.address}, is_sync=True)
    _assert_relay_success(tx, "cft.add_sanction(user_blocked)")

    tx = client.send_transaction(
        deployer, f"{AUDIT_DAPP}.CftAudit.add_sanction",
        {"addr": user_cft_kyc.address}, is_sync=True)
    _assert_relay_success(tx, "cft.add_sanction(user_cft_kyc)")

    time.sleep(2)

    return {"ct_bind_id": ct_bind_id, "app_bind_id": app_bind_id}


# ---------------------------------------------------------------------------
# IT-CC1: KYC audit on AppContract
# ---------------------------------------------------------------------------

class TestCC1KycAuditAppContract:

    def test_unapproved_user_rejected(self, client, user_blocked, env):
        _, ok = _send_tx(
            client, user_blocked,
            f"{CC_DAPP}.AppContract.sendUnorderedMessage",
            {"receiverDomain": DUMMY_DOMAIN, "receiver": DUMMY_RECEIVER,
             "message": DUMMY_MESSAGE})
        assert not ok, "Unapproved user should be rejected by KYC on AppContract"

    def test_approved_user_allowed(self, client, user_approved, env):
        _, ok = _send_tx(
            client, user_approved,
            f"{CC_DAPP}.AppContract.sendUnorderedMessage",
            {"receiverDomain": DUMMY_DOMAIN, "receiver": DUMMY_RECEIVER,
             "message": DUMMY_MESSAGE})
        assert ok, "KYC-approved user should succeed on AppContract"


# ---------------------------------------------------------------------------
# IT-CC2: CFT audit on CrossTransfer
# ---------------------------------------------------------------------------

class TestCC2CftAuditCrossTransfer:

    def test_sanctioned_user_rejected_faucet(self, client, user_blocked, env):
        _, ok = _send_tx(
            client, user_blocked,
            f"{CC_DAPP}.CrossTransfer.faucet", {})
        assert not ok, "CFT-sanctioned user should be rejected on CrossTransfer.faucet"

    def test_clean_user_allowed_faucet(self, client, user_approved, env):
        _, ok = _send_tx(
            client, user_approved,
            f"{CC_DAPP}.CrossTransfer.faucet", {})
        assert ok, "Non-sanctioned user should succeed on CrossTransfer.faucet"

    def test_clean_user_allowed_cross_transfer(self, client, user_approved, env):
        _, ok = _send_tx(
            client, user_approved,
            f"{CC_DAPP}.CrossTransfer.crossTransfer",
            {"receiverDomain": DUMMY_DOMAIN, "receiver": DUMMY_RECEIVER,
             "amount": 100})
        assert ok, "Non-sanctioned user should succeed on CrossTransfer.crossTransfer"


# ---------------------------------------------------------------------------
# IT-CC4: Cross-contract binding isolation (runs before IT-CC3 unbind)
# ---------------------------------------------------------------------------

class TestCC4BindingIsolation:

    def test_cft_sanction_no_effect_on_kyc_only_contract(
            self, client, user_cft_kyc, env):
        """CFT-sanctioned but KYC-approved user calls AppContract (KYC-only)
        -> should PASS because AppContract only checks KYC."""
        _, ok = _send_tx(
            client, user_cft_kyc,
            f"{CC_DAPP}.AppContract.sendUnorderedMessage",
            {"receiverDomain": DUMMY_DOMAIN, "receiver": DUMMY_RECEIVER,
             "message": DUMMY_MESSAGE})
        assert ok, (
            "CFT-sanctioned user with KYC approval should pass "
            "AppContract (KYC-only binding)")

    def test_no_kyc_no_effect_on_cft_only_contract(
            self, client, user_plain, env):
        """Non-KYC user without CFT sanction calls CrossTransfer (CFT-only)
        -> should PASS because CrossTransfer only checks CFT."""
        _, ok = _send_tx(
            client, user_plain,
            f"{CC_DAPP}.CrossTransfer.faucet", {})
        assert ok, (
            "Non-KYC user without CFT sanction should pass "
            "CrossTransfer (CFT-only binding)")


# ---------------------------------------------------------------------------
# IT-CC3: Unbind restores normal operation (must run last)
# ---------------------------------------------------------------------------

class TestCC3UnbindRestoresAccess:

    def test_unbind_cft_allows_sanctioned_user(
            self, client, regulator, user_blocked, env):
        client.audit_proxy_unbind(
            CORE_AUDIT_DAPP, regulator, env["ct_bind_id"], _preda_hash("cft"), sync=True)
        _, ok = _send_tx(
            client, user_blocked,
            f"{CC_DAPP}.CrossTransfer.faucet", {})
        assert ok, (
            "After unbinding CFT, sanctioned user should succeed "
            "on CrossTransfer")

    def test_unbind_kyc_allows_unapproved_user(
            self, client, regulator, user_blocked, env):
        client.audit_proxy_unbind(
            CORE_AUDIT_DAPP, regulator, env["app_bind_id"], _preda_hash("kyc"), sync=True)
        _, ok = _send_tx(
            client, user_blocked,
            f"{CC_DAPP}.AppContract.sendUnorderedMessage",
            {"receiverDomain": DUMMY_DOMAIN, "receiver": DUMMY_RECEIVER,
             "message": DUMMY_MESSAGE})
        assert ok, (
            "After unbinding KYC, unapproved user should succeed "
            "on AppContract")
