import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, ".")

from dioxide_python_sdk.client.dioxclient import DioxClient


class TestSendTransactionWithSk(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "make_request")
    def test_send_transaction_with_sk_forwards_optional_rpc_params(self, mock_make_request):
        mock_make_request.return_value = {"Hash": "fake_hash"}

        tx_hash = self.client.send_transaction_with_sk(
            private_key="fake_private_key",
            function="core.wallet.transfer",
            args={"To": "receiver:sm2", "Amount": "1", "TokenId": "DIO"},
            tokens=[{"TokenId": "DIO", "Amount": "1"}],
            isn=42,
            delegatee="demo:dapp",
            gas_price=123,
            gas_limit=456,
            ttl=789,
            sync=False,
        )

        self.assertEqual(tx_hash, "fake_hash")
        mock_make_request.assert_called_once_with(
            "tx.send_withSK",
            {
                "privatekey": "fake_private_key",
                "function": "core.wallet.transfer",
                "args": {"To": "receiver:sm2", "Amount": "1", "TokenId": "DIO"},
                "tokens": [{"TokenId": "DIO", "Amount": "1"}],
                "isn": 42,
                "delegatee": "demo:dapp",
                "gasprice": 123,
                "gaslimit": 456,
                "ttl": 789,
            },
        )


if __name__ == "__main__":
    unittest.main()
