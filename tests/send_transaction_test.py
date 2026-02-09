import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
