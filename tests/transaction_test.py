import os,sys
sys.path.append('.')

from client.dioxclient import DioxClient
from client.account import DioxAccount

client = DioxClient()

tester = DioxAccount.generate_key_pair()
print(tester.address)

unsigned_txn = client.compose_transaction(sender=tester.address,
                                          function="core.coin.mint",
                                          args={"Amount":"10000000000000000000000000000000000000000000000000"}
                                        )
print(unsigned_txn,"len:",len(unsigned_txn))

signed_txn = tester.sign_diox_transaction(unsigned_txn)
print(signed_txn,"len:",len(signed_txn))

tx_hash = client.send_raw_transaction(signed_txn,sync=True)
print(tx_hash)

tx = client.get_transaction(tx_hash)
print(tx)