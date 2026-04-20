"""§4.3.1 register — all branches."""
import pytest
from .conftest import assert_relay_success


class TestRegister:

    def test_register_first_write(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": kyc_dc, "cid": kyc_cid},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "register first write")

    def test_register_idempotent_same_cid(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": kyc_dc, "cid": kyc_cid},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "register idempotent same cid")

    def test_register_overwrite_different_cid(self, client, regulator, audit_dapp_deployed):
        cft_dc = audit_dapp_deployed["cft_dc"]
        cft_cid = audit_dapp_deployed["cft_cid"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        # First register with kyc_cid (wrong cid, just to test overwrite)
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": cft_dc, "cid": kyc_cid},
            sync=True,
        )
        # Now overwrite with correct cft_cid
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": cft_dc, "cid": cft_cid},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "register overwrite different cid")

    def test_register_rejected_invalid_argument(self, client, regulator):
        with pytest.raises(ValueError):
            client.regulation_call_audit_proxy(
                regulator, "core.AuditProxy.register",
                {"check_name": "kyc", "impl_cid": 0},
                sync=True,
            )
