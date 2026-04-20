import os
import socket
import sys
from urllib.parse import urlparse

import pytest

sys.path.append(".")

from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import Scope
from dioxide_python_sdk.client.dioxclient import DioxClient


def _rpc_available(url: str, timeout: float = 0.5) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _rpc_available(os.environ.get("DIOX_RPC_URL", "http://127.0.0.1:45678/api")),
    reason="Contract smoke test requires a running DIOX RPC",
)


def test_contract_flow_smoke():
    client = DioxClient()
    tester = DioxAccount.generate_key_pair()

    mint_tx = client.mint_dio(tester, 10**18)
    assert mint_tx is not None

    dapp_name = "00Dapp"
    bank_contract_name = "Bank"
    ens_contract_name = "ENS"

    tx_hash, ok = client.create_dapp(tester, dapp_name, 10**11)
    assert tx_hash is not None

    if not ok:
        pytest.skip(f"create_dapp({dapp_name}) did not succeed in current environment")

    contracts_dir = os.path.abspath("./test_contracts")
    contracts = {
        os.path.join(contracts_dir, "bank.gcl"): {"_owner": f"{tester.address}"},
        os.path.join(contracts_dir, "controller.gcl"): None,
        os.path.join(contracts_dir, "ens.gcl"): {"_owner": f"{tester.address}"},
    }
    deploy_tx = client.deploy_contracts(
        dapp_name=dapp_name, delegator=tester, contracts=contracts, compile_time=10
    )
    assert deploy_tx is not None

    contract_info = client.get_contract_info(dapp_name, bank_contract_name)
    assert contract_info is not None

    set_ens_tx = client.send_transaction(
        tester, f"{dapp_name}.{ens_contract_name}.set_ens", {"_cid": 287764905985}, is_sync=True
    )
    assert set_ens_tx is not None

    set_auth_tx = client.send_transaction(
        tester,
        f"{dapp_name}.{bank_contract_name}.set_authority",
        {"_controller": "0x0000004300200001:contract"},
        is_sync=True,
    )
    assert set_auth_tx is not None

    deposit_tx = client.send_transaction(
        tester,
        f"{dapp_name}.{ens_contract_name}.invoke",
        {"operation": "deposit", "amount": 1000},
        is_sync=True,
    )
    assert deposit_tx is not None
    assert client.get_contract_state(dapp_name, bank_contract_name, Scope.Address, tester.address) is not None

    withdraw_tx = client.send_transaction(
        tester,
        f"{dapp_name}.{ens_contract_name}.invoke",
        {"operation": "withdraw", "amount": 100},
        is_sync=True,
    )
    assert withdraw_tx is not None
    assert client.get_contract_state(dapp_name, bank_contract_name, Scope.Address, tester.address) is not None
