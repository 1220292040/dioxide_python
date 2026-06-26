import sys
import unittest
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, ".")

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAddress, DioxAddressType


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


class TestTransferDelegateeNormalization(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "send_transaction")
    def test_transfer_normalizes_token_symbol_delegatee(self, mock_send_transaction):
        sender = MagicMock()
        mock_send_transaction.return_value = "txhash"

        result = self.client.transfer(
            sender=sender,
            receiver="receiver",
            amount=100,
            token="TESTTKN",
            delegatee="TESTTKN",
            sync=False,
            timeout=7,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=sender,
            function="core.wallet.transfer",
            args={
                "To": "receiver",
                "Amount": "100",
                "TokenId": "TESTTKN",
            },
            delegatee="TESTTKN:token",
            is_sync=False,
            timeout=7,
        )


class TestTokenDeploymentWait(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "get_token_info")
    @patch.object(DioxClient, "get_transaction")
    @patch.object(DioxClient, "wait_for_transaction_confirmed")
    def test_wait_for_token_deployed_uses_token_state_not_refund_relay_status(
        self,
        mock_wait_for_transaction_confirmed,
        mock_get_transaction,
        mock_get_token_info,
    ):
        tx = {
            "Hash": "create-token-tx",
            "ConfirmState": "CONFIRMED",
            "Invocation": {
                "Status": "IVKRET_SUCCESS",
                "Relays": ["refund-relay:0"],
            },
        }
        mock_wait_for_transaction_confirmed.return_value = True
        mock_get_transaction.return_value = tx
        mock_get_token_info.return_value = {"TokenId": "TESTTKN"}

        result = self.client.wait_for_token_deployed("create-token-tx", 1, "TESTTKN")

        self.assertTrue(result)
        mock_get_token_info.assert_called_once_with("TESTTKN")


class TestRegulationAuditProxyCalls(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "send_transaction")
    def test_regulation_call_audit_proxy_serializes_payload(self, mock_send_transaction):
        regulator = MagicMock()

        result = self.client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.register",
            args={"audit_dc": "audit.KYC", "cid": 7},
            sync=False,
        )

        mock_send_transaction.assert_called_once()
        call = mock_send_transaction.call_args
        self.assertEqual(call.kwargs["user"], regulator)
        self.assertEqual(call.kwargs["function"], "core.regulation.call_audit_proxy")
        self.assertEqual(call.kwargs["args"]["function_name"], "core.AuditProxy.register")
        self.assertEqual(
            json.loads(call.kwargs["args"]["args_json"]),
            {"audit_dc": "audit.KYC", "cid": 7},
        )
        self.assertFalse(call.kwargs["is_sync"])
        self.assertTrue(result.ok)
        self.assertEqual(result.msg, "ok")

    @patch.object(DioxClient, "send_transaction")
    def test_regulation_call_audit_proxy_serializes_bind_payload(self, mock_send_transaction):
        regulator = MagicMock()

        result = self.client.regulation_call_audit_proxy(
            regulator=regulator,
            function_name="core.AuditProxy.bind",
            args={
                "target_dc": "app.Token",
                "audit_dc": "audit.KYC",
            },
            sync=False,
        )

        payload = json.loads(mock_send_transaction.call_args.kwargs["args"]["args_json"])
        self.assertEqual(payload["target_dc"], "app.Token")
        self.assertEqual(payload["audit_dc"], "audit.KYC")
        self.assertTrue(result.ok)

    def test_regulation_call_audit_proxy_rejects_obsolete_fields(self):
        regulator = MagicMock()

        with self.assertRaisesRegex(ValueError, "Obsolete field"):
            self.client.regulation_call_audit_proxy(
                regulator=regulator,
                function_name="core.AuditProxy.register",
                args={"check_name": "kyc", "impl_cid": 7},
                sync=False,
            )

    @patch.object(DioxClient, "get_contract_info")
    @patch.object(DioxClient, "regulation_call_audit_proxy")
    def test_register_audit_auto_queries_cid_and_delegates_to_regulation_call_audit_proxy(
        self, mock_call, mock_get_contract_info
    ):
        regulator = MagicMock()
        contract_info = MagicMock()
        contract_info.ContractID = 7
        mock_get_contract_info.return_value = contract_info
        self.client.register_audit(
            regulator=regulator,
            audit_dc="audit.KYC",
            sync=False,
        )
        mock_get_contract_info.assert_called_once_with("audit", "KYC")
        mock_call.assert_called_once_with(
            regulator=regulator,
            function_name="core.AuditProxy.register",
            args={"audit_dc": "audit.KYC", "cid": 7},
            sync=False,
            timeout=60,
        )

    @patch.object(DioxClient, "regulation_call_audit_proxy")
    def test_register_audit_uses_explicit_cid_when_provided(self, mock_call):
        regulator = MagicMock()
        self.client.register_audit(
            regulator=regulator,
            audit_dc="audit.KYC",
            cid=9,
            sync=False,
        )
        mock_call.assert_called_once_with(
            regulator=regulator,
            function_name="core.AuditProxy.register",
            args={"audit_dc": "audit.KYC", "cid": 9},
            sync=False,
            timeout=60,
        )

    @patch.object(DioxClient, "regulation_call_audit_proxy")
    def test_unregister_audit_delegates_to_regulation_call_audit_proxy(self, mock_call):
        regulator = MagicMock()
        self.client.unregister_audit(
            regulator=regulator,
            audit_dc="audit.KYC",
            sync=False,
        )
        mock_call.assert_called_once_with(
            regulator=regulator,
            function_name="core.AuditProxy.unregister",
            args={"audit_dc": "audit.KYC"},
            sync=False,
            timeout=60,
        )

    @patch.object(DioxClient, "regulation_call_audit_proxy")
    def test_bind_audit_delegates_to_regulation_call_audit_proxy(self, mock_call):
        regulator = MagicMock()
        self.client.bind_audit(
            regulator=regulator,
            target_dc="app.Token",
            audit_dc="audit.KYC",
            sync=False,
        )
        mock_call.assert_called_once_with(
            regulator=regulator,
            function_name="core.AuditProxy.bind",
            args={"target_dc": "app.Token", "audit_dc": "audit.KYC"},
            sync=False,
            timeout=60,
        )

    @patch.object(DioxClient, "regulation_call_audit_proxy")
    def test_unbind_audit_delegates_to_regulation_call_audit_proxy(self, mock_call):
        regulator = MagicMock()
        self.client.unbind_audit(
            regulator=regulator,
            target_dc="app.Token",
            audit_dc="audit.KYC",
            sync=False,
        )
        mock_call.assert_called_once_with(
            regulator=regulator,
            function_name="core.AuditProxy.unbind",
            args={"target_dc": "app.Token", "audit_dc": "audit.KYC"},
            sync=False,
            timeout=60,
        )


class TestDeployTimeoutPropagation(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "wait_for_deploy")
    @patch.object(DioxClient, "send_raw_transaction")
    @patch.object(DioxClient, "compose_transaction")
    def test_deploy_contracts_uses_extended_timeout_for_send_and_wait(
        self, mock_compose, mock_send_raw, mock_wait_for_deploy
    ):
        delegator = MagicMock()
        delegator.sign_diox_transaction.return_value = b"signed"
        mock_compose.return_value = b"unsigned"
        mock_send_raw.return_value = "txhash"

        with patch("builtins.open", unittest.mock.mock_open(read_data="contract Demo {}")):
            self.client.deploy_contracts(
                dapp_name="testa",
                delegator=delegator,
                contracts={"demo.gcl": None},
                compile_time=20,
            )

        expected_timeout = 120
        mock_send_raw.assert_called_once_with(b"signed", True, expected_timeout)
        mock_wait_for_deploy.assert_called_once_with("txhash", expected_timeout)

    @patch.object(DioxClient, "wait_for_deploy")
    @patch.object(DioxClient, "send_raw_transaction")
    @patch.object(DioxClient, "compose_transaction")
    def test_deploy_contract_uses_explicit_timeout_for_send_and_wait(
        self, mock_compose, mock_send_raw, mock_wait_for_deploy
    ):
        delegator = MagicMock()
        delegator.sign_diox_transaction.return_value = b"signed"
        mock_compose.return_value = b"unsigned"
        mock_send_raw.return_value = "txhash"

        self.client.deploy_contract(
            dapp_name="testa",
            delegator=delegator,
            source_code="contract Demo {}",
            timeout=180,
        )

        mock_send_raw.assert_called_once_with(b"signed", True, 180)
        mock_wait_for_deploy.assert_called_once_with("txhash", 180)


if __name__ == "__main__":
    unittest.main()
