
import sys
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import GLOBAL_IDENTIFIER

client = DioxClient()
cur_height = client.get_block_number()
print(cur_height)

cur_consensus_header = client.get_consensus_header_by_height(cur_height)
print(cur_consensus_header)

cur_consensus_header = client.get_consensus_header_by_hash("xcd78tmqga2ey8yy1q54c9px75f56n68dydsjm3c41g1qktmdp20")
print(cur_consensus_header)

g_transaction_block = client.get_transaction_block_by_height(GLOBAL_IDENTIFIER,cur_height)
print(g_transaction_block)

transaction_block_0 = client.get_transaction_block_by_height(0,cur_height)
print(transaction_block_0)

g_transaction_block = client.get_transaction_block_by_hash(GLOBAL_IDENTIFIER,"kzxcpsjp89hk31n44qzs99swsszdhaghej0pv24s2ta1xt037tn0")
print(g_transaction_block)


