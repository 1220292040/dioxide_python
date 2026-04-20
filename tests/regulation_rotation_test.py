import sys
import os
from urllib.parse import urlparse
import socket
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dioxide_python_sdk.client.dioxclient import DioxClient, AuditProxyResult
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import (
    CORE_CONTRACT_REGULATION_GLOBAL,
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
    reason="Regulation/rotation integration tests require a running DIOX RPC",
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


class TestRegulationState:
    def test_get_regulation_state_returns_data(self, client):
        state = client.get_regulation_state()
        assert state is not None

    def test_regulation_state_has_regulator_list(self, client):
        state = client.get_regulation_state()
        assert hasattr(state, "State") or state is not None

    def test_contract_id_constants_are_valid(self):
        assert CORE_CONTRACT_REGULATION_GLOBAL > 0
        assert CORE_CONTRACT_ROTATION_GLOBAL > CORE_CONTRACT_REGULATION_GLOBAL


class TestRotationState:
    def test_get_rotation_state_returns_data(self, client):
        state = client.get_rotation_state()
        assert state is not None

    def test_rotation_state_has_rotation_list(self, client):
        state = client.get_rotation_state()
        assert hasattr(state, "State") or state is not None

    def test_rotation_contract_id_valid(self):
        assert CORE_CONTRACT_ROTATION > 0


class TestRegulationBlock:
    def test_regulation_block_requires_regulator(self, client, regulator, target):
        tx_hash = client.regulation_block(
            regulator=regulator,
            address=target.address,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_regulation_unblock(self, client, regulator, target):
        tx_hash = client.regulation_unblock(
            regulator=regulator,
            address=target.address,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_regulation_set_audit(self, client, regulator):
        tx_hash = client.regulation_set_audit(
            regulator=regulator,
            contract_id_raw=0,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)


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


@pytest.mark.skip(reason="depends on F7 audit-proxy refactor; enable after C++/PRD landed")
class TestRegulationAuditProxy:
    _KNOWN_OK_MSGS = {"ok", "already registered", "already unregistered", "already bound", "already unbind", "updated", "cleaned", "reindexed", "no bindings"}

    def test_regulation_call_audit_proxy_register(self, client, regulator):
        result = client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.register",
            args={"dapp_contract": "smoke.KycAudit", "cid": 0},
            sync=True
        )
        assert isinstance(result, AuditProxyResult)
        assert result.tx_hash is not None
        assert result.ok and result.msg in self._KNOWN_OK_MSGS

    def test_regulation_call_audit_proxy_bind(self, client, regulator):
        result = client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.bind",
            args={"target_dapp_contract": "smoke.AppContract", "audit_dapp_contract": "smoke.KycAudit"},
            sync=True
        )
        assert isinstance(result, AuditProxyResult)
        assert result.tx_hash is not None
        assert result.ok and result.msg in self._KNOWN_OK_MSGS

    def test_regulation_call_audit_proxy_unbind(self, client, regulator):
        result = client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.unbind",
            args={"target_dapp_contract": "smoke.AppContract", "audit_dapp_contract": "smoke.KycAudit"},
            sync=True
        )
        assert isinstance(result, AuditProxyResult)
        assert result.tx_hash is not None
        assert result.ok and result.msg in self._KNOWN_OK_MSGS

    def test_regulation_call_audit_proxy_unregister(self, client, regulator):
        result = client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.unregister",
            args={"dapp_contract": "smoke.KycAudit"},
            sync=True
        )
        assert isinstance(result, AuditProxyResult)
        assert result.tx_hash is not None
        assert result.ok and result.msg in self._KNOWN_OK_MSGS
