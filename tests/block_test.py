
import sys
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import GLOBAL_IDENTIFIER

client = DioxClient()
cur_height = client.get_block_number()
print(cur_height)

cur_consensus_header = client.get_consensus_header_by_height(cur_height)
print(cur_consensus_header)

if hasattr(cur_consensus_header, 'Hash') and cur_consensus_header.Hash:
    cur_consensus_header_by_hash = client.get_consensus_header_by_hash(cur_consensus_header.Hash)
    print(cur_consensus_header_by_hash)

g_transaction_block = client.get_transaction_block_by_height(GLOBAL_IDENTIFIER,cur_height)
print(g_transaction_block)

transaction_block_0 = client.get_transaction_block_by_height(0,cur_height)
print(transaction_block_0)

if hasattr(g_transaction_block, 'Hash') and g_transaction_block.Hash:
    g_transaction_block_by_hash = client.get_transaction_block_by_hash(GLOBAL_IDENTIFIER, g_transaction_block.Hash)
    print(g_transaction_block_by_hash)


