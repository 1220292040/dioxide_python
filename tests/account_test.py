
import sys
sys.path.append('.')

from dioxide_python_sdk.client.account import DioxAccount,DioxAddress,DioxAddressType

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
assert sig is not None
assert len(sig) == 64

print(account0.verify(sig,msg))
assert account0.verify(sig,msg) is True

msg = "helloworl".encode()
print(account0.verify(sig,msg))
assert account0.verify(sig,msg) is False

key = "cqt3xyv2zb4fzwbdy8wn94akxavxk1srdvb69x8a42xsn34k1fes700f60:ed25519".encode()
addr = DioxAddress.from_key(key.decode())
print(addr,account2.address)
print(addr == account2.address)

test_sm2_json = {
    "PrivateKey": "+OfM+tj9R8I/BnIjCvc+JAdl0ADy1vAkbu0n2KINwzw=",
    "PublicKey": "AX1hRvLswVwarsbSDiQHzxmSGwR95G4DPfjnLP2oAtDr3kNsJ7X7Q5l5yhnWg/5hTe30O/CZRIbOvv94y3cmvQ==",
    "Address": "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2"
}
account_sm2 = DioxAccount.from_json(test_sm2_json)
print("SM2 Account:", account_sm2)
if account_sm2:
    print("SM2 Account Type:", account_sm2.account_type)
    print("SM2 Address:", account_sm2.address)
    print("SM2 Private Key Length:", len(account_sm2.sk_bytes))
    print("SM2 Public Key Length:", len(account_sm2.pk_bytes))
    print("SM2 Is Valid:", account_sm2.is_valid())
    assert account_sm2.account_type.name == "SM2"
    assert account_sm2.is_valid() is True

    sm2_msg = b"hello-sm2"
    sm2_sig = account_sm2.sign(sm2_msg)
    print("SM2 Signature Length:", len(sm2_sig) if sm2_sig else None)
    assert sm2_sig is not None
    assert len(sm2_sig) == 64
    assert account_sm2.verify(sm2_sig, sm2_msg) is True
    assert account_sm2.verify(sm2_sig, b"hello-sm2-bad") is False

    txdata = b"\x01\x02payload"
    signed_tx = account_sm2.sign_diox_transaction(txdata)
    print("SM2 Signed Tx Length:", len(signed_tx) if signed_tx else None)
    assert signed_tx is not None
    sid = account_sm2.account_type.value.to_bytes(1, byteorder="little")
    header = txdata + sid + account_sm2.pk_bytes
    assert signed_tx.startswith(header)
    tx_sig = signed_tx[len(header):len(header)+64]
    assert len(tx_sig) == 64
    assert account_sm2.verify(tx_sig, header) is True
    pow_part = signed_tx[len(header)+64:]
    assert len(pow_part) % 4 == 0

sm2_key = "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2"
sm2_addr = DioxAddress.from_key(sm2_key)
print("SM2 Address from_key:", sm2_addr)
if account_sm2:
    print("SM2 Address comparison:", sm2_addr == account_sm2.address if sm2_addr else False)
    assert sm2_addr == account_sm2.address
