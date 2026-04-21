"""§3.1 name-key consistency, old-field rejection, query_bindings removal."""
import hashlib
import pytest

try:
    import krock32
except ImportError:
    krock32 = None


def _sdk_hash(name: str) -> str:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    if krock32 is not None:
        encoder = krock32.Encoder()
        encoder.update(digest)
        return encoder.finalize().lower()
    return digest.hex()


class TestConsistency:

    def test_name_key_hash_consistency(self):
        """SDK hash of 'dappA.kyc' must be deterministic and non-empty."""
        h = _sdk_hash("dappA.kyc")
        assert h and len(h) > 0
        assert h == _sdk_hash("dappA.kyc"), "hash must be deterministic"
        assert _sdk_hash("dappA.kyc") != _sdk_hash("dappB.kyc"), "different names must differ"

    @pytest.mark.parametrize("bad_field,value", [
        ("check_name", "kyc"),
        ("audit_name", "kyc"),
        ("dapp_name", "dappA"),
        ("contract_name", "kyc"),
        ("impl_cid", 123),
        ("app_cid", 456),
        ("dapp_contract", "dappA.kyc"),
        ("target_dapp_contract", "appA.token"),
        ("audit_dapp_contract", "dappA.kyc"),
    ])
    def test_old_field_rejected(self, client, regulator, bad_field, value):
        with pytest.raises(ValueError, match="Obsolete field"):
            client.regulation_call_audit_proxy(
                regulator, "core.AuditProxy.register",
                {bad_field: value},
                sync=False,
            )

    def test_query_bindings_removed(self, client):
        assert not hasattr(client, "query_bindings"), \
            "query_bindings must not be exposed on DioxClient"
