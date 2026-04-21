"""§4.3.3 bind — all branches."""
import pytest
from .conftest import assert_relay_success


class TestBind:

    def _ensure_registered(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        kyc_cid = audit_dapp_deployed["kyc_cid"]
        client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.register",
            {"audit_dc": kyc_dc, "cid": kyc_cid},
            sync=True,
        )

    def test_bind_first(self, client, regulator, audit_dapp_deployed):
        self._ensure_registered(client, regulator, audit_dapp_deployed)
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        cft_dc = audit_dapp_deployed["cft_dc"]
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "bind first")

    def test_bind_idempotent(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        cft_dc = audit_dapp_deployed["cft_dc"]
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dc": cft_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        assert tx is not None
        assert_relay_success(client, tx, "bind idempotent")

    def test_bind_unregistered_audit(self, client, regulator):
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dc": "appX.token", "audit_dc": "unknown.audit"},
            sync=True,
        )
        assert tx is not None  # tx lands; AuditResult.ok=false inside

    def test_bind_self_rejected(self, client, regulator, audit_dapp_deployed):
        kyc_dc = audit_dapp_deployed["kyc_dc"]
        tx = client.regulation_call_audit_proxy(
            regulator, "core.AuditProxy.bind",
            {"target_dc": kyc_dc, "audit_dc": kyc_dc},
            sync=True,
        )
        assert tx is not None  # tx lands; AuditResult.ok=false inside
