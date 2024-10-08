
from client.dioxclient import DioxClient
from client.account import DioxAccount
from utils.gadget import title_info

client = DioxClient()
# client.generate_key_pair()
title_info("get_overview")
print(client.get_overview())

title_info("get_block_number")
print(client.get_block_number())

title_info("get_shard_index")
print(client.get_shard_index("global",None))
print(client.get_shard_index("shard",0))
print(client.get_shard_index("address","zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519"))
print(client.get_shard_index("uint256","234"))

title_info("get_isn")
print(client.get_isn("zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519"))

title_info("get_consensus_header_by_height")
print(client.get_consensus_header_by_height(50))

title_info("get_consensus_header_by_hash")
print(client.get_consensus_header_by_hash("2x7jt9mckbtyakramr78j8q0y7aey2v1hshct59yxynryddev3d0"))

title_info("get_transaction_block_by_height")
print(client.get_transaction_block_by_height(1,50))

title_info("get_transaction_block_by_hash")
print(client.get_transaction_block_by_hash(1,"emybse4q65g1xfjvz9fk50fqh5vcb1hnm1zmmz67xxv5krtf5s60"))

title_info("get_transaction")
print(client.get_transaction("xn3bm3z0r2pcvqkvmtdasvj993fwr7m0vjtx7eb5zft1x8xprdjg"))
