
from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import Scope
from dioxide_python_sdk.utils.gadget import title_info
from dioxide_python_sdk.config.client_config import Config
import sys
import time

client = DioxClient()

title_info("check node connection")
print(f"Connecting to: {Config.rpc_url}")
try:
    overview = client.get_overview()
    if overview:
        print(f"Connected to node: {overview.get('VesionName', 'Unknown')}")
        print(f"Block height: {overview.get('HeadHeight', 'Unknown')}")
    else:
        print(f"Error: Cannot connect to Dioxide node at {Config.rpc_url}")
        print("Please start the Dioxide node first.")
        sys.exit(1)
except Exception as e:
    print(f"Error: Cannot connect to Dioxide node - {e}")
    print(f"Please ensure the node is running at {Config.rpc_url}")
    print("You can change the URL in: dioxide_python_sdk/config/client_config.py")
    sys.exit(1)

# Create an account
title_info("create an account")
pk = "WTKi+W99TEEt153Zt8isUznwXqYkA0aVWEbd7edk6AvivGov5hBLJLQbS2hk8bnC3FM8Et6+Axaw1uukce+ZEQ=="
account = DioxAccount.from_key(pk)
print(account)

# Mint some tokens
title_info("mint some tokens")
result = client.mint_dio(account, 10**18)
if result:
    print(result)
else:
    print("Failed to mint tokens")

# Use unique dapp name to avoid conflicts (max 8 chars)
# Use last 2 digits of timestamp for uniqueness
timestamp_suffix = str(int(time.time()))[-2:]
dapp_name = f"Dapp{timestamp_suffix}"
bank_contract_name = "Bank"
ens_contract_name = "ENS"

# Create dapp
title_info("create dapp")
print(f"Creating dapp: {dapp_name} (max 8 chars)")
result = client.create_dapp(account, dapp_name, 10**12)
if result:
    tx_hash, _ = result
    print(tx_hash)
else:
    print("Failed to create dapp")
    sys.exit(1)

# Deploy contracts
# Note: Deployment order will be determined by dependency analysis
# bank.gcl (no dependencies) → controller.gcl (imports Bank) → ens.gcl (imports Controller)
constructors = [{"_owner":account.address},None,{"_owner":account.address}]

title_info("deploy contract / contracts")
print("Constructor args (in dependency order):")
print(f"  [0] bank.gcl: {constructors[0]}")
print(f"  [1] controller.gcl: {constructors[1]}")
print(f"  [2] ens.gcl: {constructors[2]}")
print("\nContract dependencies:")
print("  - bank.gcl: no imports")
print("  - controller.gcl: imports Bank")
print("  - ens.gcl: imports Controller")
print("\nSDK will automatically deploy in dependency order\n")

try:
    deploy_tx_hash = client.deploy_contracts(
        dapp_name=dapp_name,
        delegator=account,
        dir_path="./test_contracts",
        construct_args=constructors,
        compile_time=20
    )

    if deploy_tx_hash:
        print(f"✓ Deploy transaction: {deploy_tx_hash}")
    else:
        print("\n[WARNING] deploy_contracts returned None")
        print("Possible causes:")
        print("  1. Contract inter-dependency compilation error")
        print("  2. Constructor argument parsing error")
        print("  3. Node compilation service timeout")
        print("\nAlternative: Deploy contracts using node CLI tool")
        print("See doc/CONTRACT_DEPLOYMENT.md for more details")
except Exception as e:
    print(f"\n[ERROR] Exception during deployment: {e}")
    print("See doc/CONTRACT_DEPLOYMENT.md for troubleshooting")

# Verify deployment
title_info("verify contract deployment")
bank_contract_info = client.get_contract_info(dapp_name, bank_contract_name)
ens_contract_info = client.get_contract_info(dapp_name, ens_contract_name)

if not bank_contract_info:
    print(f"✗ {bank_contract_name} contract not found")
    print("Cannot proceed without contracts. Exiting...")
    sys.exit(0)
else:
    print(f"✓ {bank_contract_name} contract verified")

if not ens_contract_info:
    print(f"✗ {ens_contract_name} contract not found")
    print("Cannot proceed without contracts. Exiting...")
    sys.exit(0)
else:
    print(f"✓ {ens_contract_name} contract verified")

# Contract info
title_info("contract info")
print(f"{bank_contract_name} details:")
print(bank_contract_info)

# Invoke contract
title_info("invoke contract")

print("Step 1: Set ENS contract ID...")
tx1 = client.send_transaction(account,"{}.{}.{}".format(dapp_name,ens_contract_name,"set_ens"),{"_cid":287764905985},is_sync=True)
if tx1:
    print(f"  ✓ set_ens tx: {tx1}")
else:
    print("  ✗ set_ens failed")

print("Step 2: Set Bank authority...")
tx2 = client.send_transaction(account,"{}.{}.{}".format(dapp_name,bank_contract_name,"set_authority"),{"_controller":"0x0000004300200001:contract"},is_sync=True)
if tx2:
    print(f"  ✓ set_authority tx: {tx2}")
else:
    print("  ✗ set_authority failed")

print("Step 3: Deposit 1000...")
tx3 = client.send_transaction(account,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"deposit","amount":1000},is_sync=True)
if tx3:
    print(f"  ✓ deposit tx: {tx3}")
    state = client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,account.address)
    if state:
        print(f"  Balance after deposit: {state}")
else:
    print("  ✗ deposit failed")

print("Step 4: Withdraw 100...")
tx_hash = client.send_transaction(account,"{}.{}.{}".format(dapp_name,ens_contract_name,"invoke"),{"operation":"withdraw","amount":100},is_sync=True)
if tx_hash:
    print(f"  ✓ withdraw tx: {tx_hash}")
    state = client.get_contract_state(dapp_name,bank_contract_name,Scope.Address,account.address)
    if state:
        print(f"  Balance after withdraw: {state}")
else:
    print("  ✗ withdraw failed")

# Get event
if tx_hash:
    title_info("filter contract event")
    events = client.get_events_by_transaction(tx_hash)
    if events:
        for event in events:
            print(f"Event name: {event.Target}")
            print(f"Event input: {event.Input}")
    else:
        print("No events found")
else:
    print("Skip event filtering due to transaction failure")


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
