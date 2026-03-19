"""
Delegated token transfer test cases.
"""

import pytest
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount


class TestDelegatedTokenTransfer:
    """Delegated token transfer test class."""

    def setup_method(self):
        """Setup before each test."""
        self.client = DioxClient()
        self.creator_pk = "pCrlpQ/VSj9pDbHGwdRJx9+Ck/26/LPnVbbUjDi7kfHqdcqDTB8Dd34vpQB4RUO4fP0eQIDAxTYwF/7a6gIr0w=="
        self.creator_account = DioxAccount.from_key(self.creator_pk)
        
        self.sender_pk = "vJ2Pl7cXhr0TiIORl3Sfgfq+BPsIKEtIGF85mRd4fjHKZbnANBWRXPfHxvB44KuN3S/fqMLxjBxz6hA9vxKrMg=="
        self.sender_account = DioxAccount.from_key(self.sender_pk)
        
        self.receiver_pk = "WTKi+W99TEEt153Zt8isUznwXqYkA0aVWEbd7edk6AvivGov5hBLJLQbS2hk8bnC3FM8Et6+Axaw1uukce+ZEQ=="
        self.receiver_account = DioxAccount.from_key(self.receiver_pk)

    def test_delegated_token_transfer(self):
        """Test delegated token transfer."""
        
        token_symbol = "TESTTKN"
        
        print(f"\nStep 1: Mint DIO for creator account")
        mint_tx = self.client.mint_dio(self.creator_account, 10**18, sync=True, timeout=60)
        assert mint_tx is not None, "Mint DIO should succeed"
        
        print(f"Step 2: Create token: {token_symbol}")
        tx_hash, ok = self.client.create_token(
            user=self.creator_account,
            symbol=token_symbol,
            initial_supply="10000",
            deposit="100000000",
            decimals=10,
            sync=True,
            timeout=60
        )
        assert tx_hash is not None, "Create token should return tx hash"
        assert ok is True, "Token should be deployed successfully"
        
        print(f"Step 3: Verify token info")
        token_info = self.client.get_token_info(token_symbol)
        assert token_info is not None, "Token info should be available"
        print(f"Token info: {token_info}")
        
        print(f"Step 4: Transfer token from creator to sender")
        transfer_tx1 = self.client.transfer(
            sender=self.creator_account,
            receiver=self.sender_account.address,
            amount=1000,
            token=token_symbol,
            sync=True,
            timeout=60
        )
        assert transfer_tx1 is not None, "First transfer should succeed"
        
        print(f"Step 5: Delegated token transfer from sender to receiver")
        transfer_tx2 = self.client.transfer(
            sender=self.sender_account,
            receiver=self.receiver_account.address,
            amount=100,
            token=token_symbol,
            delegatee=token_symbol,
            sync=True,
            timeout=60
        )
        assert transfer_tx2 is not None, "Delegated transfer should succeed"
        
        print(f"Step 6: Verify transaction")
        tx_obj = self.client.get_transaction(transfer_tx2)
        assert tx_obj is not None, "Transaction should be retrievable"
        print(f"Transaction function: {tx_obj.Function}")
        print(f"Transaction status: {tx_obj.Invocation.Status if hasattr(tx_obj, 'Invocation') else 'N/A'}")
        
        assert self.client.is_tx_success(tx_obj), "Delegated transfer transaction should be successful"
        
        print(f"\n✓ Delegated token transfer test passed!")

    def test_regular_token_transfer_without_delegatee(self):
        """Test regular token transfer without delegatee parameter."""
        
        print(f"\nStep 1: Regular DIO transfer (backward compatibility test)")
        tx_hash = self.client.transfer(
            sender=self.creator_account,
            receiver=self.sender_account.address,
            amount=10,
            token="DIO",
            sync=True,
            timeout=60
        )
        
        assert tx_hash is not None, "Regular transfer should work without delegatee parameter"
        print(f"✓ Backward compatibility test passed!")
