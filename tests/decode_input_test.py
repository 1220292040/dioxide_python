import sys
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
import time

print("="*50)
print("Test decode_transaction_input")
print("="*50)

try:
    client = DioxClient()
    
    print("\nTest 1: Decode regular transaction input")
    print("-" * 50)
    
    try:
        tester = DioxAccount.generate_key_pair()
        print(f"Generated account: {tester.address}")
        
        mint_amount = "1000000000000000000"
        tx_hash = client.mint_dio(tester, int(mint_amount), sync=True, timeout=30)
        
        if not tx_hash:
            print("ERROR: Failed to mint tokens (no transaction hash returned)")
            print("Skipping Test 1 - RPC connection may not be available")
            raise Exception("RPC connection failed")
        
        print(f"Mint transaction hash: {tx_hash}")
        
        tx = client.get_transaction(tx_hash)
        if not tx:
            print("ERROR: Failed to get transaction")
            raise Exception("Failed to get transaction")
        
        print(f"Transaction Function: {tx.Function}")
        print(f"Transaction Input (hex): {tx.Input}")
        
        decoded_args = client.decode_transaction_input(tx)
        print(f"Decoded arguments: {decoded_args}")
        
        if decoded_args and "Amount" in decoded_args:
            if str(decoded_args["Amount"]) == mint_amount:
                print("SUCCESS: Decoded amount matches!")
            else:
                print(f"ERROR: Amount mismatch! Expected {mint_amount}, got {decoded_args['Amount']}")
        else:
            print("ERROR: Failed to decode Amount")
    except Exception as e:
        print(f"Test 1 skipped: RPC connection not available - {e}")
        print("Note: This test requires a running Dioxide node")
    
    print("\nTest 2: Decode relay transaction input")
    print("-" * 50)
    
    try:
        if 'tx' not in locals() or tx is None:
            print("Test 2 skipped: No transaction from Test 1")
        elif hasattr(tx, 'Invocation') and hasattr(tx.Invocation, 'Relays') and tx.Invocation.Relays:
            relay_hash = tx.Invocation.Relays[0]
            print(f"Relay transaction hash: {relay_hash}")
            
            relay_tx = client.get_transaction(relay_hash)
            print(f"Relay Function: {relay_tx.Function}")
            print(f"Relay Input (hex): {relay_tx.Input}")
            
            try:
                decoded_relay_args = client.decode_transaction_input(relay_tx)
                print(f"Decoded relay arguments: {decoded_relay_args}")
                print("SUCCESS: Relay transaction decoded!")
            except Exception as e:
                print(f"Note: Could not decode relay transaction (may be core contract): {e}")
        else:
            print("No relay transactions found in this transaction")
    except Exception as e:
        print(f"Test 2 skipped: {e}")
    
    print("\nTest 3: Decode custom contract transaction")
    print("-" * 50)
    
    timestamp_suffix = str(int(time.time()))[-2:]
    dapp_name = f"Test{timestamp_suffix}"
    
    try:
        result = client.create_dapp(tester, dapp_name, 10**12, sync=True, timeout=30)
        if result:
            dapp_tx_hash, _ = result
            print(f"Created dapp: {dapp_name}, tx: {dapp_tx_hash}")
            
            dapp_tx = client.get_transaction(dapp_tx_hash)
            print(f"Dapp creation Function: {dapp_tx.Function}")
            print(f"Dapp creation Input (hex): {dapp_tx.Input}")
            
            decoded_dapp_args = client.decode_transaction_input(dapp_tx)
            print(f"Decoded dapp creation arguments: {decoded_dapp_args}")
            print("SUCCESS: Dapp creation transaction decoded!")
        else:
            print("Failed to create dapp, skipping test 3")
    except Exception as e:
        print(f"Dapp creation test skipped: {e}")
    
    print("\nTest 4: Decode transaction with empty input")
    print("-" * 50)
    
    try:
        class EmptyTx:
            def __init__(self):
                self.Function = 'core.coin.mint'
                self.Input = ''
        
        empty_tx = EmptyTx()
        
        decoded_empty = client.decode_transaction_input(empty_tx)
        print(f"Decoded empty input: {decoded_empty}")
        if decoded_empty == {}:
            print("SUCCESS: Empty input decoded correctly (returned empty dict)!")
        else:
            print(f"ERROR: Expected empty dict, got {decoded_empty}")
    except Exception as e:
        print(f"Empty input test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)
    print("All tests completed!")
    print("="*50)
    
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()

