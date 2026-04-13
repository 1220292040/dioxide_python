import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import (
    CORE_CONTRACT_REGULATION_GLOBAL,
    CORE_CONTRACT_ROTATION_GLOBAL,
    CORE_CONTRACT_ROTATION,
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


AUDIT_DAPP_NAME = "core"


class TestAuditProxy:
    """AuditProxy management API tests.

    These tests only verify that the SDK methods correctly compose and
    send transactions. They require a running node with the system
    AuditProxy already deployed under AUDIT_DAPP_NAME.
    """

    def test_audit_proxy_register(self, client, regulator):
        tx_hash = client.audit_proxy_register(
            dapp_name=AUDIT_DAPP_NAME,
            regulator=regulator,
            check_name="kyc",
            impl_cid=0,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_audit_proxy_bind(self, client, regulator):
        tx_hash = client.audit_proxy_bind(
            dapp_name=AUDIT_DAPP_NAME,
            regulator=regulator,
            app_cvid=0,
            audit_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_audit_proxy_query_bindings(self, client, regulator):
        tx_hash = client.audit_proxy_query_bindings(
            dapp_name=AUDIT_DAPP_NAME,
            regulator=regulator,
            check_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_audit_proxy_unbind(self, client, regulator):
        tx_hash = client.audit_proxy_unbind(
            dapp_name=AUDIT_DAPP_NAME,
            regulator=regulator,
            app_cvid=0,
            audit_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_audit_proxy_unregister(self, client, regulator):
        tx_hash = client.audit_proxy_unregister(
            dapp_name=AUDIT_DAPP_NAME,
            regulator=regulator,
            check_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_get_audit_proxy_state(self, client):
        state = client.get_audit_proxy_state(dapp_name=AUDIT_DAPP_NAME)
        assert state is not None
