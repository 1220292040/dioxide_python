"""
Unit test for relay hash normalization logic

Tests the _normalize_relay_hash function without requiring full SDK dependencies.
This test can be run independently to verify the core normalization logic.
"""


def normalize_relay_hash(relay_hash):
    """
    Normalize relay hash by removing GroupIndex suffix if present.
    
    Relay hash from Relays array may have format:
    - hash:GroupIndex (when GroupIndex <= 250)
    - hash (when GroupIndex > 250)
    
    RPC interface only accepts pure hash without GroupIndex suffix.
    
    Args:
        relay_hash: Relay hash string, possibly with :GroupIndex suffix
        
    Returns:
        Pure hash string without GroupIndex suffix
    """
    if ':' in relay_hash:
        base, suffix = relay_hash.rsplit(':', 1)
        if suffix.isdigit():
            return base
    return relay_hash


def test_normalize_relay_hash():
    """Test relay hash normalization with various inputs"""
    test_cases = [
        # (input, expected_output, description)
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
    
    print("Testing normalize_relay_hash()...")
    print("=" * 80)
    
    all_passed = True
    for input_hash, expected_output, description in test_cases:
        result = normalize_relay_hash(input_hash)
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
        print("\nThe normalization logic correctly handles:")
        print("  - Relay hashes with GroupIndex suffix (hash:0, hash:5, etc.)")
        print("  - Pure hashes without suffix")
        print("  - Edge cases (non-numeric suffix, multiple colons)")
        return True
    else:
        print("Some tests FAILED!")
        return False


def main():
    print("Relay Hash Normalization Unit Test")
    print("=" * 80)
    print()
    print("Problem: Relay hashes from Relays array may include GroupIndex suffix")
    print("         (e.g., hash:0), but RPC interface only accepts pure hash.")
    print()
    print("Solution: Strip GroupIndex suffix before querying transactions.")
    print()
    
    success = test_normalize_relay_hash()
    
    print("\n" + "=" * 80)
    if success:
        print("RESULT: Normalization logic is correct!")
        return 0
    else:
        print("RESULT: Normalization logic has issues")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
