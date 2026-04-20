"""Shared fixtures for F7 audit-proxy regulation tests."""
import os
import sys
import uuid
from urllib.parse import urlparse
import socket

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dioxide_python_sdk.client.dioxclient import DioxClient, AuditProxyResult
from dioxide_python_sdk.client.account import DioxAccount

REG_CONTRACTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "oxd_bc", "rvm_contracts")
)

REGULATOR_KEY_B64 = "6NHi+B1jWQ3gDfC2GFHHBoNPEhCWa9lkIUMGRtRc2LbYtNrHang1QL/XdXt0pSAVw0v4cX7iDz55Ksnf41cIfA=="

_SUFFIX = uuid.uuid4().hex[:4]
AUDIT_DAPP = f"F7{_SUFFIX}"
TARGET_DAPP = f"TG{_SUFFIX}"


def _rpc_available(url: str, timeout: float = 0.5) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_regulation_rpc_available():
    rpc_url = os.environ.get("DIOX_RPC_URL", "http://127.0.0.1:45678/api")
    if not _rpc_available(rpc_url):
        pytest.skip(f"Regulation integration tests require RPC at {rpc_url}")


@pytest.fixture(scope="session")
def client():
    rpc_url = os.environ.get("DIOX_RPC_URL", "http://127.0.0.1:45678/api")
    ws_url = os.environ.get("DIOX_WS_URL", rpc_url.replace("http", "ws", 1))
    return DioxClient(url=rpc_url, ws_url=ws_url)


@pytest.fixture(scope="session")
def regulator(client):
    acc = DioxAccount.from_key(REGULATOR_KEY_B64)
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="session")
def deployer(client):
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="session")
def audit_dapp_deployed(client, deployer):
    """Deploy KycAudit and CftAudit under AUDIT_DAPP; return dapp_contract strings and cids."""
    _, ok = client.create_dapp(deployer, AUDIT_DAPP, 10**12)
    assert ok, f"Failed to create audit dapp {AUDIT_DAPP}"

    contracts = {
        os.path.join(REG_CONTRACTS_DIR, "kyc_audit.prd"): None,
        os.path.join(REG_CONTRACTS_DIR, "cft_audit.prd"): None,
    }
    tx = client.deploy_contracts(AUDIT_DAPP, deployer, contracts, compile_time=20)
    assert tx is not None, "Audit contracts deploy failed"

    kyc_info = client.get_contract_info(AUDIT_DAPP, "KycAudit")
    cft_info = client.get_contract_info(AUDIT_DAPP, "CftAudit")
    return {
        "kyc_dc": f"{AUDIT_DAPP}.KycAudit",
        "cft_dc": f"{AUDIT_DAPP}.CftAudit",
        "kyc_cid": kyc_info.ContractID,
        "cft_cid": cft_info.ContractID,
    }


def assert_relay_success(client, result, label=""):
    tx_hash = result.tx_hash if isinstance(result, AuditProxyResult) else result
    assert tx_hash is not None, f"{label}: tx_hash is None"
    tx_detail = client.get_transaction(tx_hash)
    assert client.is_tx_success(tx_detail), f"{label}: initial tx failed"
    relays = client.get_all_relay_transactions(tx_detail, detail=True)
    for r in relays:
        assert r.Invocation.Status == "IVKRET_SUCCESS", \
            f"{label} relay failed: {r.Invocation.Status}"
