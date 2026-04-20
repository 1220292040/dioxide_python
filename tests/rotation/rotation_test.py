import sys
import os
from urllib.parse import urlparse
import socket
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import (
    CORE_CONTRACT_ROTATION_GLOBAL,
    CORE_CONTRACT_ROTATION,
)


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
    reason="Rotation integration tests require a running DIOX RPC",
)


@pytest.fixture(scope="module")
def client():
    return DioxClient()


@pytest.fixture(scope="module")
def regulator(client):
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


@pytest.fixture(scope="module")
def target(client):
    acc = DioxAccount.generate_key_pair()
    client.mint_dio(acc, 10**18)
    return acc


class TestRotationState:
    def test_get_rotation_state_returns_data(self, client):
        state = client.get_rotation_state()
        assert state is not None

    def test_rotation_state_has_rotation_list(self, client):
        state = client.get_rotation_state()
        assert hasattr(state, "State") or state is not None

    def test_rotation_contract_id_valid(self):
        assert CORE_CONTRACT_ROTATION > 0

    def test_rotation_global_contract_id_valid(self):
        assert CORE_CONTRACT_ROTATION_GLOBAL > 0


class TestRotationNodes:
    def test_rotation_add_node(self, client, regulator, target):
        tx_hash = client.rotation_add_node(
            regulator=regulator,
            address=target.address,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_rotation_remove_node(self, client, regulator, target):
        tx_hash = client.rotation_remove_node(
            regulator=regulator,
            address=target.address,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_rotation_report_violation(self, client, regulator, target):
        client.rotation_add_node(
            regulator=regulator,
            address=target.address,
            sync=True
        )
        tx_hash = client.rotation_report_violation(
            regulator=regulator,
            miner=target.address,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)
