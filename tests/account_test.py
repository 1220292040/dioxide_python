
import os,sys
sys.path.append('.')

from client.dioxaccount import DioxAccount,DioxAddress,DioxAddressType

account0 = DioxAccount.generate_key_pair()
print(account0)

test_json = {
    "PrivateKey": "X7I0csd+4QfRXD2KMQjoOweXEXJHE2s6T/wiBz5Gil37KvY6ywVu43Q58q+OW7c3jAeef7EKgaAGCbF76nlr2A==",
    "PublicKey": "+yr2OssFbuN0OfKvjlu3N4wHnn+xCoGgBgmxe+p5a9g=",
    "Address": "zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519",
    "Shard": 1
}
account1 = DioxAccount.from_json(test_json)
print(account1)


"""
{
    "PrivateKey": "77+mc+VQxh2vkbnu6oAxJlsJcXKv4vv4qKamnSXC39Jl9D77YvrI//Ft8jlUkVPqt9mHOG7WZPUKILuajJML3Q==",
    "PublicKey": "ZfQ++2L6yP/xbfI5VJFT6rfZhzhu1mT1CiC7moyTC90=",
    "Address": "cqt3xyv2zb4fzwbdy8wn94akxavxk1srdvb69x8a42xsn34k1fes700f60:ed25519",
    "Shard": 2
}
"""
test_sk_b64 = "77+mc+VQxh2vkbnu6oAxJlsJcXKv4vv4qKamnSXC39Jl9D77YvrI//Ft8jlUkVPqt9mHOG7WZPUKILuajJML3Q=="
account2 = DioxAccount.from_key(test_sk_b64)
print(account2)


for d in ["ab","abcd","abcdefgha","asd_asf","ads@#sf"]:
    dapp_address = DioxAddress(None,DioxAddressType.DAPP)
    if dapp_address.set_delegatee_from_string(d):
        print(dapp_address)
    else:
        print("invalid dapp:{}".format(d))

for d in ["ab","abcd","abcdefgha","ABCD","Ab@A"]:
    token_address = DioxAddress(None,DioxAddressType.TOKEN)
    if token_address.set_delegatee_from_string(d):
        print(token_address)
    else:
        print("invalid token:{}".format(d))

for d in ["ab","abcd","abcdefgha"]:
    name_address = DioxAddress(None,DioxAddressType.NAME)
    if name_address.set_delegatee_from_string(d):
        print(name_address)
    else:
        print("invalid name:{}".format(d))


msg = "helloworld".encode()
sig = account0.sign(msg)
print(sig)

print(account0.verify(sig,msg))

msg = "helloworl".encode()
print(account0.verify(sig,msg))
