# Dioxide Python SDK
Welcome to Dioxide Python SDK! This SDK provides developers with a set of tools and functionalities to simplify your development process in dioxide.

## Install
```shell
git clone https://github.com/1220292040/diox_python_sdk.git
cd diox_python_sdk
python setup.py install
```
## Features
- Feature 1: get on-chain infos by sdk
> With SDK, you can access a variety of on-chain information, such as transactions, blocks, shard index, contract state and more.

- Feature 2: create an account, compose or sign transactions
> With SDK, you can also create a valid account, and send transactions.


## Usage
in your project, you can use sdk as :
```python
# demo.py

from dioxide_python_sdk.client.dioxclient import DioxClient

#create a client
client = DioxClient()

######################### get some info from dioxide blockchain ##########################

# get overview
print(client.get_overview())

#get block_number
print(client.get_block_number())

#get shard_index
print(client.get_shard_index("global",None))
print(client.get_shard_index("shard",0))
print(client.get_shard_index("address","zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519"))
print(client.get_shard_index("uint256","234"))

#get isn
print(client.get_isn("zcnfcepb0nqe6x1syaqrwpxq6y60f7kzp458380616rqqtksdfc26pvh1c:ed25519"))

#get block by height
print(client.get_consensus_header_by_height(50))
print(client.get_transaction_block_by_height(1,50))

#get block by hash
print(client.get_consensus_header_by_hash("2x7jt9mckbtyakramr78j8q0y7aey2v1hshct59yxynryddev3d0"))
print(client.get_transaction_block_by_hash(1,"emybse4q65g1xfjvz9fk50fqh5vcb1hnm1zmmz67xxv5krtf5s60"))

#get transaction
print(client.get_transaction("xn3bm3z0r2pcvqkvmtdasvj993fwr7m0vjtx7eb5zft1x8xprdjg"))


######################### deploy contract and send transactions or get contract states ###########################
#mint some tokens 
print(client.mint_dio(tester,10**18))

dapp_name = "00Dapp"
bank_contract_name = "Bank"
ens_contract_name = "ENS"

#Create dapp
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
    #deploy contract / contracts
    print(client.deploy_contracts(dapp_name=dapp_name,delegator=tester,dir_path="./test_contracts",construct_args=constructors))
    if client.wait_for_contract_deployed(dapp_name,bank_contract_name):
        print("deploy success")
    else:
        print("deploy fail")
else:
    print("error")
contract_info = client.get_contract_info(dapp_name,bank_contract_name)
print(contract_info)

#invoke
client.send_transaction(tester,"{}.{}.{}".format(dapp_name,ens_contract_name,"set_ens"),{"_cid":287764905985},is_sync=True)
client.send_transaction(tester,"{}.{}.{}".format(dapp_name,bank_contract_name,"set_authority"),{"_controller":"0x0000004300200001:contract"},is_sync=True)
client.send_transaction(tester,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"deposit","amount":1000},is_sync=True)

#get state
print(client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,tester.address))

client.send_transaction(tester,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"withdraw","amount":100},is_sync=True)
print(client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,tester.address))

######################### subscribe some infos ###########################
def handler(r):
    print(r)

def filter1(r):
    if r["Height"] > 10 and r["Height"]<20:
        return True
    else:
        return False

def filter2(r):
    if r["Height"] > 20:
        return True
    else:
        return False

threads = []
for topic in ["consensus_header", "transaction_block"]:
    t = threading.Thread(target=client.subscribe, args=(topic, handler, None))
    threads.append(t)
    t.start()

start = time.time()

while True:
    print("main thread => pause...")
    time.sleep(1)
    if time.time() - start > 10:
        client.unsubscribe(threads[1].ident)
```
