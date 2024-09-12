
from client.dioxclient import DioxClient
from client.dioxaccount import DioxAccount
print("start")
client = DioxClient()
# client.generate_key_pair()

print(client.get_block_number())
print(client.get_shard_index("address","1dapp:dapp"))

account = DioxAccount.generate_key_pair()
print(account)

test_json = {
    "PrivateKey": "o+mlwBT6mZPkTbHjBHNdwfZ+VQnCRa3qPBvZX+qDf0Lgka6GQE5ONrd2cHbiS8ys5PylZejE+TP5Inv39uiAPA==",
    "PublicKey": "4JGuhkBOTja3dnB24kvMrOT8pWXoxPkz+SJ79/bogDw=",
    "Address": "w28tx1j09s73ddvpe1ve4jycnkjfs9b5x32fjczs49xzfxq8g0y86dwhg8:ed25519",
}

test_sk_b64 = "77+mc+VQxh2vkbnu6oAxJlsJcXKv4vv4qKamnSXC39Jl9D77YvrI//Ft8jlUkVPqt9mHOG7WZPUKILuajJML3Q=="

account1 = DioxAccount.from_json(test_json)
print(account1)

account2 = DioxAccount.from_key(test_sk_b64)
print(account2)