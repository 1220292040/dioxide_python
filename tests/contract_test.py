import os,sys
sys.path.append('.')

from client.dioxclient import DioxClient
from client.account import DioxAccount,DioxAddress,DioxAddressType


client = DioxClient()

tester = DioxAccount.generate_key_pair()
print(tester.address)

print(client.mint_dio(tester,10**18))

dapp_name = "dappE"
tx_hash,ok = client.create_dapp(tester,dapp_name,10**11)
print(tx_hash)

if ok:
    constructors = [
        {
            "_owner":"{}".format(tester.address)
        },
        None,
        {
            "_owner":"{}".format(tester.address)
        }
    ]
    print(client.deploy_contracts(dapp_name=dapp_name,delegatee=tester,dir_path="./test_contracts",construct_args=constructors))
else:
    print("error")