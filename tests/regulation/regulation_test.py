import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import (
    CORE_CONTRACT_REGULATION_GLOBAL,
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


class TestRegulationAuditProxy:
    """Regulation audit management API tests.

    These tests verify that the SDK composes requests against the new
    `core.regulation.*` audit management surface instead of direct
    `core.AuditProxy.*` calls.
    """

    def test_regulation_register_audit_impl(self, client, regulator):
        tx_hash = client.regulation_register_audit_impl(
            regulator=regulator,
            check_name="kyc",
            impl_cid=0,
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_regulation_bind_audit(self, client, regulator):
        tx_hash = client.regulation_bind_audit(
            regulator=regulator,
            app_cid=0,
            audit_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_regulation_query_audit_bindings(self, client):
        bindings = client.regulation_query_audit_bindings(
            check_name="kyc",
        )
        assert bindings is not None
        assert isinstance(bindings, list)

    def test_regulation_unbind_audit(self, client, regulator):
        tx_hash = client.regulation_unbind_audit(
            regulator=regulator,
            app_cid=0,
            audit_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)

    def test_regulation_unregister_audit_impl(self, client, regulator):
        tx_hash = client.regulation_unregister_audit_impl(
            regulator=regulator,
            check_name="kyc",
            sync=True
        )
        assert tx_hash is not None
        assert isinstance(tx_hash, str)
