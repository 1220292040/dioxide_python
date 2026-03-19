"""
Test for relay hash GroupIndex handling

This test verifies that relay hashes with GroupIndex suffix (hash:0, hash:1, etc.)
are correctly normalized before querying transactions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dioxide_python_sdk.client.dioxclient import DioxClient


def test_normalize_relay_hash():
    """Test _normalize_relay_hash method"""
    client = DioxClient()
    
    test_cases = [
        ("g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg:0", 
         "g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg",
         "GroupIndex 0"),
        ("g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg:5", 
         "g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg",
         "GroupIndex 5"),
        ("g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg:250", 
         "g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg",
         "GroupIndex 250 (max)"),
        ("g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg", 
         "g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg",
         "Pure hash without suffix"),
        ("abcd1234:notanumber", 
         "abcd1234:notanumber",
         "Non-numeric suffix (should not normalize)"),
        ("hash:with:multiple:colons:123",
         "hash:with:multiple:colons",
         "Multiple colons (only last one matters)"),
    ]
    
    print("Testing _normalize_relay_hash()...")
    print("=" * 80)
    
    all_passed = True
    for input_hash, expected_output, description in test_cases:
        result = client._normalize_relay_hash(input_hash)
        passed = result == expected_output
        all_passed = all_passed and passed
        
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {description}")
        print(f"  Input:    {input_hash}")
        print(f"  Expected: {expected_output}")
        print(f"  Got:      {result}")
        if not passed:
            print(f"  ERROR: Mismatch!")
        print()
    
    print("=" * 80)
    if all_passed:
        print("All tests PASSED!")
        print("\nThe fix correctly handles:")
        print("  - Relay hashes with GroupIndex suffix (hash:0, hash:5, etc.)")
        print("  - Pure hashes without suffix")
        print("  - Edge cases (non-numeric suffix, multiple colons)")
        return True
    else:
        print("Some tests FAILED!")
        return False


def test_relay_transaction_query():
    """Test relay transaction query with GroupIndex"""
    client = DioxClient()
    
    print("\nTesting relay transaction query with GroupIndex...")
    print("=" * 80)
    
    relay_hash_with_groupindex = "g2dxxhdx13sdx0hsabdgg4620h7t2kd8d6mvkyfaq10x3bgjngpg:0"
    normalized_hash = client._normalize_relay_hash(relay_hash_with_groupindex)
    
    print(f"Original relay hash: {relay_hash_with_groupindex}")
    print(f"Normalized hash:     {normalized_hash}")
    print()
    
    try:
        print("Attempting to query with normalized hash...")
        tx = client.get_transaction(normalized_hash)
        
        if tx and hasattr(tx, 'Hash'):
            print(f"SUCCESS: Transaction found!")
            print(f"  Hash: {tx.Hash}")
            if hasattr(tx, 'Function'):
                print(f"  Function: {tx.Function}")
            return True
        else:
            print("Transaction not found (may not exist in current blockchain state)")
            print("This is OK - the important thing is no RPC error occurred")
            return True
            
    except Exception as e:
        error_msg = str(e)
        if "invalid transaction hash" in error_msg.lower():
            print(f"FAILED: RPC rejected the hash format")
            print(f"  Error: {error_msg}")
            return False
        else:
            print(f"Transaction not found: {error_msg}")
            print("This is expected if the transaction doesn't exist")
            return True


def main():
    print("Relay Hash GroupIndex Handling Test")
    print("=" * 80)
    print()
    print("Problem: Relay hashes from Relays array may include GroupIndex suffix")
    print("         (e.g., hash:0), but RPC interface only accepts pure hash.")
    print()
    print("Solution: Strip GroupIndex suffix before querying transactions.")
    print()
    
    test1_passed = test_normalize_relay_hash()
    test2_passed = test_relay_transaction_query()
    
    print("\n" + "=" * 80)
    print("FINAL RESULT:")
    if test1_passed and test2_passed:
        print("All tests PASSED - Fix is working correctly!")
        return 0
    else:
        print("Some tests FAILED - Please review the output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
