
from client.dioxclient import DioxClient
from client.account import DioxAccount
print("start")
client = DioxClient()
# client.generate_key_pair()

print(client.get_block_number())
s = client.get_shard_index("addres","1dapp:dapp")