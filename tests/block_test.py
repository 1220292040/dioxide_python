import sys

sys.path.append(".")

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import GLOBAL_IDENTIFIER


def test_block_queries_smoke():
    client = DioxClient()
    cur_height = client.get_block_number()
    assert cur_height is not None

    cur_consensus_header = client.get_consensus_header_by_height(cur_height)
    assert cur_consensus_header is not None

    if hasattr(cur_consensus_header, "Hash") and cur_consensus_header.Hash:
        cur_consensus_header_by_hash = client.get_consensus_header_by_hash(cur_consensus_header.Hash)
        assert cur_consensus_header_by_hash is not None

    g_transaction_block = client.get_transaction_block_by_height(GLOBAL_IDENTIFIER, cur_height)
    assert g_transaction_block is not None

    transaction_block_0 = client.get_transaction_block_by_height(0, cur_height)
    assert transaction_block_0 is not None

    if hasattr(g_transaction_block, "Hash") and g_transaction_block.Hash:
        g_transaction_block_by_hash = client.get_transaction_block_by_hash(
            GLOBAL_IDENTIFIER, g_transaction_block.Hash
        )
        assert g_transaction_block_by_hash is not None
