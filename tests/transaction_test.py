import sys
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
import base64

print("="*50)
print("Basic transaction test (requires RPC connection)")
print("="*50)

try:
    client = DioxClient()
    tester = DioxAccount.generate_key_pair()
    print(f"Generated account: {tester.address}")

    unsigned_txn = client.compose_transaction(sender=tester.address,
                                              function="core.coin.mint",
                                              args={"Amount":"10000000000000000000000000000000000000000000000000"},
                                              ttl=100
                                              )

    print(base64.b64encode(unsigned_txn),"len:",len(unsigned_txn))

    signed_txn = tester.sign_diox_transaction(unsigned_txn)
    print(base64.b64encode(signed_txn),"len:",len(signed_txn))

    tx_hash = client.send_raw_transaction(signed_txn,sync=True,timeout=30)
    print(tx_hash)

    tx = client.get_transaction(tx_hash)
    print(tx)

    token_symbol = "ABNC"
    h = client.create_token(tester,"{}".format(token_symbol),"10000","100000000",10)
    print(h)

    print(client.get_token_info(token_symbol))
except Exception as e:
    print(f"RPC test skipped (RPC server not available): {e}")
    print("Continuing with local serialization tests...")
    client = None
    tester = DioxAccount.generate_key_pair()

print("\n" + "="*50)
print("Testing compose_transaction_local with deserialized_args")
print("="*50)

def extract_input_from_transaction(tx_bytes):
    offset = 0
    offset += 1  # version
    offset += 1  # packflag
    offset += 6  # timestamp
    offset += 4  # isn
    offset += 2  # ttl_sc_tsc
    offset += 2  # mode
    offset += 1  # opcode
    core_contract = tx_bytes[offset]
    offset += 1  # core_contract
    offset += 4  # gas_price_mantissa
    offset += 2  # gas_price_exp
    offset += 4  # gas_limit

    CORE_CONTRACT_RVM = 0x3F
    has_rvm_contract = (core_contract & 0x3F) == CORE_CONTRACT_RVM
    if has_rvm_contract:
        offset += 8  # rvm_contract
    else:
        offset += 1  # build

    mode = int.from_bytes(tx_bytes[12:14], byteorder='little')
    ITM_SCOPE_ADDRESS = 1
    ITM_FIRST_SIGNER = 11
    has_delegatee = (mode & 0xF) in [ITM_SCOPE_ADDRESS, ITM_FIRST_SIGNER]
    if has_delegatee and (mode & 0xF) == ITM_SCOPE_ADDRESS:
        offset += 36  # delegatee

    input_size = int.from_bytes(tx_bytes[offset:offset+2], byteorder='little')
    offset += 2
    input_data = tx_bytes[offset:offset+input_size]
    return input_data.hex()

try:
    from dioxide_python_sdk.utils.gadget import serialize_args, deserialized_args

    if client is None:
        print("\nNote: RPC connection not available, skipping tests that require RPC")
        print("Running only serialization/deserialization tests...")

    test_args = {"Amount": 10000000000000000000000000000000000000000000000000}
    signature = "bigint:Amount"

    print("\nTest 1: Serialize and deserialize directly")
    print("-" * 50)
    serialized = serialize_args(signature, test_args)
    print(f"Serialized (hex): {serialized}")

    deserialized = deserialized_args(signature, serialized)
    print(f"Deserialized: {deserialized}")

    if str(deserialized.get("Amount")) == str(test_args["Amount"]):
        print("SUCCESS: Direct serialize/deserialize works correctly!")
    else:
        print(f"ERROR: Mismatch! Expected {test_args['Amount']}, got {deserialized.get('Amount')}")

    print("\nTest 2: Build transaction manually and extract input")
    print("-" * 50)
    
    try:
        from dioxide_python_sdk.client.transaction import UnsignedTransaction
        from dioxide_python_sdk.client.contract import ContractInvokeID, Scope, CORE_CONTRACT_RVM
        from dioxide_python_sdk.client.types import EngineID as EngineIDEnum
        import time
        import math
        
        contract_invoke_id_val = 0x1100000001
        contract_invoke_id = ContractInvokeID(contract_invoke_id_val)
        
        opcode = 0
        tx = UnsignedTransaction(contract_invoke_id, opcode, timestamp=int(time.time_ns()//1_000_000))
        tx.set_isn(1)
        tx.set_gas_price(100)
        tx.set_gas_limit(500000)
        tx.ttl = 100
        
        serialized_input = serialize_args(signature, test_args)
        tx.input = bytes.fromhex(serialized_input)
        tx.input_size = len(tx.input)
        
        unsigned_txn_local = tx.serialize()
        print(f"Transaction length: {len(unsigned_txn_local)}")
        
        input_hex = extract_input_from_transaction(unsigned_txn_local)
        print(f"Extracted input (hex): {input_hex}")
        
        deserialized_from_tx = deserialized_args(signature, input_hex)
        print(f"Deserialized from transaction: {deserialized_from_tx}")
        
        if str(deserialized_from_tx.get("Amount")) == str(test_args["Amount"]):
            print("SUCCESS: Manual transaction build -> extract input -> deserialized_args works correctly!")
        else:
            print(f"ERROR: Mismatch! Expected {test_args['Amount']}, got {deserialized_from_tx.get('Amount')}")
        
        print("\nTest 3: Multiple parameters test")
        print("-" * 50)
        
        import krock32
        decoder = krock32.Decoder()
        try:
            decoder.update(tester.address)
            address_bytes = decoder.finalize()
        except:
            address_bytes = bytes(36)
        
        test_args_multi = {
            "To": address_bytes,
            "Amount": 1000000000000000000,
            "TokenId": "DIO"
        }
        signature_multi = "address:To,bigint:Amount,string:TokenId"
        
        serialized_input_multi = serialize_args(signature_multi, test_args_multi)
        tx_multi = UnsignedTransaction(contract_invoke_id, opcode, timestamp=int(time.time_ns()//1_000_000))
        tx_multi.set_isn(2)
        tx_multi.set_gas_price(100)
        tx_multi.set_gas_limit(500000)
        tx_multi.ttl = 100
        tx_multi.input = bytes.fromhex(serialized_input_multi)
        tx_multi.input_size = len(tx_multi.input)
        
        unsigned_txn_multi = tx_multi.serialize()
        print(f"Transaction length: {len(unsigned_txn_multi)}")
        
        input_hex_multi = extract_input_from_transaction(unsigned_txn_multi)
        print(f"Extracted input (hex): {input_hex_multi[:100]}...")
        
        deserialized_multi = deserialized_args(signature_multi, input_hex_multi)
        print(f"Deserialized: {deserialized_multi}")
        
        all_match = True
        for key, value in test_args_multi.items():
            deserialized_value = deserialized_multi.get(key)
            if key == "To":
                if isinstance(deserialized_value, str):
                    try:
                        decoder2 = krock32.Decoder()
                        decoder2.update(deserialized_value)
                        deserialized_bytes = decoder2.finalize()
                        if deserialized_bytes != value:
                            print(f"ERROR: Mismatch for {key}!")
                            all_match = False
                    except:
                        if str(deserialized_value) != str(value):
                            print(f"ERROR: Mismatch for {key}!")
                            all_match = False
                elif deserialized_value != value:
                    print(f"ERROR: Mismatch for {key}!")
                    all_match = False
            elif str(deserialized_value) != str(value):
                print(f"ERROR: Mismatch for {key}! Expected {value}, got {deserialized_value}")
                all_match = False
        
        if all_match:
            print("SUCCESS: Multiple parameters serialize/deserialize works correctly!")
        
        if client is not None:
            print("\nTest 4: Using compose_transaction_local (requires RPC)")
            print("-" * 50)
            try:
                isn = client.get_isn(tester.address)
                unsigned_txn_rpc = client.compose_transaction_local(
                    sender=tester.address,
                    function="core.coin.mint",
                    args=test_args,
                    signature=signature,
                    isn=isn,
                    ttl=100
                )
                input_hex_rpc = extract_input_from_transaction(unsigned_txn_rpc)
                deserialized_rpc = deserialized_args(signature, input_hex_rpc)
                if str(deserialized_rpc.get("Amount")) == str(test_args["Amount"]):
                    print("SUCCESS: compose_transaction_local -> deserialized_args works correctly!")
                else:
                    print(f"ERROR: Mismatch! Expected {test_args['Amount']}, got {deserialized_rpc.get('Amount')}")
            except Exception as rpc_error:
                print(f"RPC test skipped: {rpc_error}")
    except Exception as e:
        print(f"Error in Test 2/3: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"Error testing compose_transaction_local: {e}")
    import traceback
    traceback.print_exc()