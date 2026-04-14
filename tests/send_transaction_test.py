import sys
import unittest
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")

from dioxide_python_sdk.client.dioxclient import DioxClient


class TestGetTransactionGroupRelayHash(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "make_request")
    def test_get_transaction_with_group_relay_hash_format_normalizes_hash_and_shard(
        self, mock_make_request
    ):
        fake_tx = {"Hash": "abc123", "ConfirmState": "CONFIRMED", "Invocation": {"Relays": []}}
        mock_make_request.return_value = fake_tx

        result = self.client.get_transaction("abc123:0")

        mock_make_request.assert_called_once()
        call_args = mock_make_request.call_args
        self.assertEqual(call_args[0][0], "dx.transaction")
        params = call_args[0][1]
        self.assertEqual(params.get("hash"), "abc123", "hash should be normalized without ':0'")
        self.assertEqual(params.get("shard_index"), 0, "shard_index should be parsed from hash")

    @patch.object(DioxClient, "make_request")
    def test_get_transaction_plain_hash_unchanged(self, mock_make_request):
        fake_tx = {"Hash": "plainhash", "ConfirmState": "CONFIRMED", "Invocation": {"Relays": []}}
        mock_make_request.return_value = fake_tx

        self.client.get_transaction("plainhash")

        params = mock_make_request.call_args[0][1]
        self.assertEqual(params.get("hash"), "plainhash")
        self.assertNotIn("shard_index", params)


class TestRegulationAuditProxyCalls(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "send_transaction")
    def test_regulation_call_audit_proxy_serializes_payload(self, mock_send_transaction):
        regulator = MagicMock()

        self.client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.register",
            args={"check_name": "kyc", "impl_cid": 7},
            sync=False,
        )

        mock_send_transaction.assert_called_once()
        call = mock_send_transaction.call_args
        self.assertEqual(call.kwargs["user"], regulator)
        self.assertEqual(call.kwargs["function"], "core.regulation.call_audit_proxy")
        self.assertEqual(call.kwargs["args"]["function_name"], "core.AuditProxy.register")
        self.assertEqual(
            json.loads(call.kwargs["args"]["args_json"]),
            {"check_name": self.client._normalize_preda_hash("kyc"), "impl_cid": 7},
        )
        self.assertFalse(call.kwargs["is_sync"])

    @patch.object(DioxClient, "regulation_call_audit_proxy")
    def test_regulation_register_audit_impl_uses_generic_call(self, mock_generic_call):
        regulator = MagicMock()

        self.client.regulation_register_audit_impl(
            regulator=regulator,
            check_name="kyc",
            impl_cid=9,
            sync=True,
        )

        mock_generic_call.assert_called_once()
        call = mock_generic_call.call_args
        self.assertEqual(call.kwargs["regulator"], regulator)
        self.assertEqual(call.kwargs["function_name"], "core.AuditProxy.register")
        self.assertEqual(call.kwargs["args"]["impl_cid"], 9)
        self.assertIn("check_name", call.kwargs["args"])

    @patch.object(DioxClient, "send_transaction")
    def test_regulation_call_audit_proxy_normalizes_bind_audit_name(self, mock_send_transaction):
        regulator = MagicMock()

        self.client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.bind",
            args={"app_cid": 3, "audit_name": "kyc"},
            sync=True,
        )

        payload = json.loads(mock_send_transaction.call_args.kwargs["args"]["args_json"])
        self.assertEqual(payload["app_cid"], 3)
        self.assertEqual(payload["audit_name"], self.client._normalize_preda_hash("kyc"))


if __name__ == "__main__":
    unittest.main()
