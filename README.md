# Dioxide Python SDK
Welcome to Dioxide Python SDK! This SDK provides developers with a set of tools and functionalities to simplify your development process in dioxide.

## Install
```shell
git clone https://github.com/1220292040/dioxide_python.git
cd dioxide_python
pip install -r requirements.txt
pip install .
```
## Features
- Feature 1: get on-chain infos by sdk
> With SDK, you can access a variety of on-chain information, such as transactions, blocks, shard index, contract state and more.

- Feature 2: create an account, compose or sign transactions
> With SDK, you can also create a valid account, and send transactions.


## Usage
in your project, you can use sdk as :

python demo.py
```python
# demo.py


from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import Scope
from dioxide_python_sdk.utils.gadget import title_info

client = DioxClient()

# #create an account
title_info("create an account")
pk = "WTKi+W99TEEt153Zt8isUznwXqYkA0aVWEbd7edk6AvivGov5hBLJLQbS2hk8bnC3FM8Et6+Axaw1uukce+ZEQ=="
account = DioxAccount.from_key(pk)
print(account)

# # mint some tokens 
title_info("mint some tokens")
print(client.mint_dio(account, 10**18))

dapp_name = "00Dapp"
bank_contract_name = "Bank"
ens_contract_name = "ENS"

# Create dapp
title_info("create dapp")
tx_hash, _ = client.create_dapp(account, dapp_name, 10**12)
print(tx_hash)

# order by contracts
constructors = [{"_owner":account.address},None,{"_owner":account.address}]

# #deploy contract / contracts
title_info("deploy contract / contracts")
client.deploy_contracts(dapp_name=dapp_name,delegator=account,dir_path="./test_contracts",construct_args=constructors,compile_time=10)

# #contract info
title_info("contract info")
contract_info = client.get_contract_info(dapp_name,bank_contract_name)
print(contract_info)

#invoke contract
title_info("invoke contract")
client.send_transaction(account,"{}.{}.{}".format(dapp_name,ens_contract_name,"set_ens"),{"_cid":287764905985},is_sync=True)
client.send_transaction(account,"{}.{}.{}".format(dapp_name,bank_contract_name,"set_authority"),{"_controller":"0x0000004300200001:contract"},is_sync=True)
client.send_transaction(account,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"deposit","amount":1000},is_sync=True)
print(client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,account.address))

tx_hash = client.send_transaction(account,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"withdraw","amount":100},is_sync=True)
print(client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,account.address))

#get event
title_info("filter contract event")
events = client.get_events_by_transaction(tx_hash)
for event in events:
    print(f"name: {event.Target}")
    print(f"input: {event.Input}")
    #parse input args TODO


# title_info("get_overview")
# print(client.get_overview())

# title_info("get_block_number")
# print(client.get_block_number())

# title_info("get_shard_index")
# print(client.get_shard_index("global",None))
# print(client.get_shard_index("shard",0))
# print(client.get_shard_index("address","zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519"))
# print(client.get_shard_index("uint256","234"))

# title_info("get_isn")
# print(client.get_isn("zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519"))

# title_info("get_consensus_header_by_height")
# print(client.get_consensus_header_by_height(50))

# title_info("get_consensus_header_by_hash")
# print(client.get_consensus_header_by_hash("2x7jt9mckbtyakramr78j8q0y7aey2v1hshct59yxynryddev3d0"))

# title_info("get_transaction_block_by_height")
# print(client.get_transaction_block_by_height(1,50))

# title_info("get_transaction_block_by_hash")
# print(client.get_transaction_block_by_hash(1,"emybse4q65g1xfjvz9fk50fqh5vcb1hnm1zmmz67xxv5krtf5s60"))

# title_info("get_transaction")
# print(client.get_transaction("xn3bm3z0r2pcvqkvmtdasvj993fwr7m0vjtx7eb5zft1x8xprdjg"))

