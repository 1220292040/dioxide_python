import os,sys
sys.path.append('.')

from client.dioxclient import DioxClient
from client.account import DioxAccount,DioxAddress,DioxAddressType


client = DioxClient()

tester = DioxAccount.generate_key_pair()
print(tester.address)

print(client.mint_dio(tester,10**18))

dapp_name = "dappD"
tx_hash,ok = client.create_dapp(tester,dapp_name,10**11)
print(tx_hash)
dapp_address = DioxAddress(None,DioxAddressType.DAPP)
dapp_address.set_delegatee_from_string(dapp_name)

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
    print(client.deploy_contracts(dapp_address=dapp_address.address,delegatee=tester,dir_path="D:\python_workspace\dioxide_python_sdk\\test_contracts",construct_args=constructors))
else:
    print("error")