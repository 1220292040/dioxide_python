
from client.dioxclient import DioxClient
from client.dioxaccount import DioxAccount
print("start")
client = DioxClient()
# client.generate_key_pair()

print(client.get_block_number())
s = client.get_shard_index("addres","1dapp:dapp")