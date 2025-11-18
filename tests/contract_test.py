import sys
import os
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import Scope

client = DioxClient()

tester = DioxAccount.generate_key_pair()
print(tester.address)

print(client.mint_dio(tester,10**18))

dapp_name = "00Dapp"
bank_contract_name = "Bank"
ens_contract_name = "ENS"

#create dapp
tx_hash,ok = client.create_dapp(tester,dapp_name,10**11)
print(tx_hash)

if ok:
    contracts_dir = os.path.abspath("./test_contracts")
    contracts = {
        os.path.join(contracts_dir, "bank.gcl"): {"_owner": "{}".format(tester.address)},
        os.path.join(contracts_dir, "controller.gcl"): None,
        os.path.join(contracts_dir, "ens.gcl"): {"_owner": "{}".format(tester.address)}
    }
    client.deploy_contracts(dapp_name=dapp_name,delegator=tester,contracts=contracts,compile_time=10)

    #contract info
    contract_info = client.get_contract_info(dapp_name,bank_contract_name)
    print(contract_info)

    #invoke
    client.send_transaction(tester,"{}.{}.{}".format(dapp_name,ens_contract_name,"set_ens"),{"_cid":287764905985},is_sync=True)
    client.send_transaction(tester,"{}.{}.{}".format(dapp_name,bank_contract_name,"set_authority"),{"_controller":"0x0000004300200001:contract"},is_sync=True)
    client.send_transaction(tester,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"deposit","amount":1000},is_sync=True)
    print(client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,tester.address))

    client.send_transaction(tester,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"withdraw","amount":100},is_sync=True)
    print(client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,tester.address))

