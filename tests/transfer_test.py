"""
Transfer test cases.
"""

import pytest
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount


class TestTransfer:
    """Transfer test class."""

    def setup_method(self):
        """Setup before each test."""
        self.client = DioxClient()
        self.sender_pk = "pCrlpQ/VSj9pDbHGwdRJx9+Ck/26/LPnVbbUjDi7kfHqdcqDTB8Dd34vpQB4RUO4fP0eQIDAxTYwF/7a6gIr0w=="
        self.sender_account = DioxAccount.from_key(self.sender_pk)
        self.receiver_pk = "vJ2Pl7cXhr0TiIORl3Sfgfq+BPsIKEtIGF85mRd4fjHKZbnANBWRXPfHxvB44KuN3S/fqMLxjBxz6hA9vxKrMg=="
        self.receiver_account = DioxAccount.from_key(self.receiver_pk)

    def test_transfer_dio_token(self):
        """Test DIO token transfer."""
        # Execute transfer
        tx_hash = self.client.transfer(
            self.sender_account,
            self.receiver_account.address,
            10,
            token="DIO",
            sync=True,
            timeout=60
        )

        # Assert tx hash is not empty
        assert tx_hash is not None, "Transfer should return tx hash"
        assert isinstance(tx_hash, str), "Tx hash should be string"
        assert len(tx_hash) > 0, "Tx hash should not be empty"

        # Assert accounts are created
        assert self.sender_account is not None, "Sender account should be created"
        assert self.receiver_account is not None, "Receiver account should be created"
