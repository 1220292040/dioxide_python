"""
Delegated Token Transfer Example

This example demonstrates how to use the delegated token transfer feature
to transfer tokens on behalf of a token contract.

This is a standalone example script that can be run directly to test
the delegated token transfer functionality.
"""

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount


def main():
    client = DioxClient()
    
    print("=" * 60)
    print("Delegated Token Transfer Example")
    print("=" * 60)
    
    creator_pk = "pCrlpQ/VSj9pDbHGwdRJx9+Ck/26/LPnVbbUjDi7kfHqdcqDTB8Dd34vpQB4RUO4fP0eQIDAxTYwF/7a6gIr0w=="
    user_b_pk = "vJ2Pl7cXhr0TiIORl3Sfgfq+BPsIKEtIGF85mRd4fjHKZbnANBWRXPfHxvB44KuN3S/fqMLxjBxz6hA9vxKrMg=="
    user_c_pk = "WTKi+W99TEEt153Zt8isUznwXqYkA0aVWEbd7edk6AvivGov5hBLJLQbS2hk8bnC3FM8Et6+Axaw1uukce+ZEQ=="
    
    creator_account = DioxAccount.from_key(creator_pk)
    user_b_account = DioxAccount.from_key(user_b_pk)
    user_c_account = DioxAccount.from_key(user_c_pk)
    
    print(f"\nAccounts:")
    print(f"  Creator: {creator_account.address}")
    print(f"  User B:  {user_b_account.address}")
    print(f"  User C:  {user_c_account.address}")
    
    token_symbol = "MYTOKEN"
    
    print(f"\n{'Step 1: Mint DIO for creator':-^60}")
    try:
        tx_hash = client.mint_dio(creator_account, 10**18, sync=True, timeout=60)
        print(f"✓ Minted DIO, tx: {tx_hash}")
    except Exception as e:
        print(f"✗ Failed to mint DIO: {e}")
        return
    
    print(f"\n{'Step 2: Create Token':-^60}")
    try:
        tx_hash, ok = client.create_token(
            user=creator_account,
            symbol=token_symbol,
            initial_supply="10000",
            deposit="100000000",
            decimals=10,
            sync=True,
            timeout=60
        )
        if ok:
            print(f"✓ Token created: {token_symbol}")
            print(f"  Transaction: {tx_hash}")
        else:
            print(f"✗ Token creation failed")
            return
    except Exception as e:
        print(f"✗ Failed to create token: {e}")
        return
    
    print(f"\n{'Step 3: Transfer token to User B':-^60}")
    try:
        tx_hash = client.transfer(
            sender=creator_account,
            receiver=user_b_account.address,
            amount=1000,
            token=token_symbol,
            sync=True,
            timeout=60
        )
        print(f"✓ Transferred 1000 {token_symbol} to User B")
        print(f"  Transaction: {tx_hash}")
    except Exception as e:
        print(f"✗ Failed to transfer: {e}")
        return
    
    print(f"\n{'Step 4: Delegated Transfer (B -> C)':-^60}")
    print(f"User B transfers {token_symbol} to User C using delegated mode")
    print(f"Delegatee: {token_symbol} (token address)")
    try:
        tx_hash = client.transfer(
            sender=user_b_account,
            receiver=user_c_account.address,
            amount=100,
            token=token_symbol,
            delegatee=token_symbol,
            sync=True,
            timeout=60
        )
        print(f"✓ Delegated transfer successful!")
        print(f"  Transaction: {tx_hash}")
        
        tx_obj = client.get_transaction(tx_hash)
        if tx_obj:
            print(f"  Function: {tx_obj.Function}")
            if hasattr(tx_obj, 'Invocation'):
                print(f"  Status: {tx_obj.Invocation.Status}")
    except Exception as e:
        print(f"✗ Delegated transfer failed: {e}")
        return
    
    print(f"\n{'Step 5: Regular Transfer (backward compatibility)':-^60}")
    print(f"Regular DIO transfer without delegatee parameter")
    try:
        tx_hash = client.transfer(
            sender=creator_account,
            receiver=user_b_account.address,
            amount=10,
            token="DIO",
            sync=True,
            timeout=60
        )
        print(f"✓ Regular transfer successful!")
        print(f"  Transaction: {tx_hash}")
    except Exception as e:
        print(f"✗ Regular transfer failed: {e}")
        return
    
    print(f"\n{'='*60}")
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
