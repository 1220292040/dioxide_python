import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount


class TestDeployContractNoArgs(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()
        self.delegator = MagicMock(spec=DioxAccount)
        self.dapp_name = "testdapp"
        self.dummy_code = "contract C {}"

    @patch.object(DioxClient, "wait_for_deploy")
    @patch.object(DioxClient, "send_raw_transaction", return_value="fake_tx_hash")
    @patch.object(DioxClient, "compose_transaction")
    def test_deploy_contract_no_construct_args_sends_empty_cargs(
        self, mock_compose, mock_send_raw, mock_wait
    ):
        mock_compose.return_value = b"unsigned_txn_bytes"
        self.delegator.sign_diox_transaction.return_value = b"signed_txn"

        self.client.deploy_contract(
            self.dapp_name,
            self.delegator,
            source_code=self.dummy_code,
            construct_args=None,
        )

        mock_compose.assert_called_once()
        call_kwargs = mock_compose.call_args[1]
        self.assertIn("args", call_kwargs)
        args = call_kwargs["args"]
        self.assertIn("cargs", args)
        self.assertEqual(args["cargs"], [""], "No-arg contract should send cargs as [\"\"], not [\"null\"]")

    @patch.object(DioxClient, "wait_for_deploy")
    @patch.object(DioxClient, "send_raw_transaction", return_value="fake_tx_hash")
    @patch.object(DioxClient, "compose_transaction")
    def test_deploy_contract_with_construct_args_sends_json_cargs(
        self, mock_compose, mock_send_raw, mock_wait
    ):
        mock_compose.return_value = b"unsigned_txn_bytes"
        self.delegator.sign_diox_transaction.return_value = b"signed_txn"
        construct_args = {"_owner": "addr123"}

        self.client.deploy_contract(
            self.dapp_name,
            self.delegator,
            source_code=self.dummy_code,
            construct_args=construct_args,
        )

        call_kwargs = mock_compose.call_args[1]
        args = call_kwargs["args"]
        self.assertEqual(args["cargs"], ['{"_owner": "addr123"}'])


if __name__ == "__main__":
    unittest.main()
