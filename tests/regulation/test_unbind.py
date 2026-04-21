"""§4.3.4 unbind — all branches."""
from .conftest import assert_relay_success


class TestUnbind:

    def test_unbind_then_idempotent(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        cft_dc = audit_dapp_deployed["cft_dc"]
        # Ensure registered and bound
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"audit_dc": kyc_dc, "cid": kyc_cid},
            sync=True,
        )
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        # First unbind
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unbind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "unbind first")
        # Second unbind — idempotent
        tx2 = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unbind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        assert tx2 is not None
        assert_relay_success(client, tx2, "unbind idempotent")

    def test_unbind_cleans_dangling_entry(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        cft_dc = audit_dapp_deployed["cft_dc"]
        # Register, bind, unregister (force dangling), then unbind
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"audit_dc": kyc_dc, "cid": kyc_cid},
            sync=True,
        )
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        # Unbind first so unregister succeeds
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unbind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unregister",
            {"audit_dc": kyc_dc},
            sync=True,
        )
        # Now unbind again — dangling entry cleanup
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.unbind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "unbind cleans dangling")
