import os,sys
sys.path.append('.')

from client.dioxclient import DioxClient
from client.account import DioxAccount
import base64

client = DioxClient()

tester = DioxAccount.generate_key_pair()
print(tester.address)

unsigned_txn = client.compose_transaction(sender=tester.address,
                                          function="core.coin.mint",
                                          args={"Amount":"10000000000000000000000000000000000000000000000000"}
                                        )

print(base64.b64encode(unsigned_txn),"len:",len(unsigned_txn))

signed_txn = tester.sign_diox_transaction(unsigned_txn)
print(base64.b64encode(signed_txn),"len:",len(signed_txn))

tx_hash = client.send_raw_transaction(signed_txn,sync=True,timeout=30)
print(tx_hash)

tx = client.get_transaction(tx_hash)
print(tx)

token_symbol = "ABNC"
h = client.create_token(tester,"{}".format(token_symbol),"10000","100000000",10)
print(h)

print(client.get_token_info(token_symbol))