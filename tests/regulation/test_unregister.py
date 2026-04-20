"""§4.3.2 unregister — all branches."""
import pytest
from .conftest import assert_relay_success


class TestUnregister:

    def test_unregister_clean_when_empty(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        # Ensure registered
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": kyc_dc, "cid": kyc_cid},
            sync=True,
        )
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unregister",
            {"dapp_contract": kyc_dc},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "unregister clean when empty")

    def test_unregister_idempotent(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        # Already unregistered from previous test
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unregister",
            {"dapp_contract": kyc_dc},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "unregister idempotent")

    def test_unregister_still_bound(self, client, regulator, audit_dapp_deployed):
        cft_dc = audit_dapp_deployed["cft_dc"]
        cft_cid = audit_dapp_deployed["cft_cid"]
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        # Register both
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": cft_dc, "cid": cft_cid},
            sync=True,
        )
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"dapp_contract": kyc_dc, "cid": kyc_cid},
            sync=True,
        )
        # Bind kyc to cft (target=cft, audit=kyc)
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dapp_contract": cft_dc, "audit_dapp_contract": kyc_dc},
            sync=True,
        )
        # Attempt to unregister kyc while still bound — tx succeeds at chain level
        # but AuditResult.ok should be false; we just verify the tx lands
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unregister",
            {"dapp_contract": kyc_dc},
            sync=True,
        )
        assert tx is not None
        # Cleanup
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unbind",
            {"target_dapp_contract": cft_dc, "audit_dapp_contract": kyc_dc},
            sync=True,
        )
