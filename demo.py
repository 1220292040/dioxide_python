from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.account import DioxAccount
from dioxide_python_sdk.client.contract import Scope
from dioxide_python_sdk.utils.gadget import title_info
from dioxide_python_sdk.config.client_config import Config
import sys
import time
import os

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
        sys.exit(1)
except Exception as e:
    print(f"Error: Cannot connect to Dioxide node - {e}")
    sys.exit(1)

title_info("create an account")
pk = "WTKi+W99TEEt153Zt8isUznwXqYkA0aVWEbd7edk6AvivGov5hBLJLQbS2hk8bnC3FM8Et6+Axaw1uukce+ZEQ=="
account = DioxAccount.from_key(pk)
print(account)

title_info("mint some tokens")
result = client.mint_dio(account, 10**18)
if result:
    print(result)
else:
    print("Failed to mint tokens")

# Use unique dapp name (max 8 chars)
timestamp_suffix = str(int(time.time()))[-2:]
dapp_name = f"Dapp{timestamp_suffix}"
bank_contract_name = "Bank"
controller_contract_name = "Controller"
ens_contract_name = "ENS"

title_info("create dapp")
print(f"Creating dapp: {dapp_name}")
result = client.create_dapp(account, dapp_name, 10**12)
if result:
    tx_hash, _ = result
    print(tx_hash)
else:
    print("Failed to create dapp")
    sys.exit(1)

title_info("deploy contracts")
contracts_dir = os.path.abspath("./test_contracts")
contracts = {
    os.path.join(contracts_dir, "bank.gcl"): {"_owner": account.address},
    os.path.join(contracts_dir, "controller.gcl"): None,
    os.path.join(contracts_dir, "ens.gcl"): {"_owner": account.address}
}

try:
    deploy_tx_hash = client.deploy_contracts(
        dapp_name=dapp_name,
        delegator=account,
        contracts=contracts,
        compile_time=20
    )
    if deploy_tx_hash:
        print(f"✓ Deploy transaction: {deploy_tx_hash}")
    else:
        print("Deploy failed")
        sys.exit(1)
except Exception as e:
    print(f"Deploy error: {e}")
    sys.exit(1)

title_info("verify deployment")
controller_contract_info = client.get_contract_info(dapp_name, controller_contract_name)

if not controller_contract_info:
    print("Contract deployment verification failed")
    sys.exit(1)

controller_cid = controller_contract_info.get('ContractVersionID')

title_info("setup contracts")
tx1 = client.send_transaction(account, f"{dapp_name}.{ens_contract_name}.set_ens", {"_cid": controller_cid}, is_sync=True)
if not tx1:
    print("✗ set_ens failed")
    sys.exit(1)

controller_address = f"0x{controller_cid:016X}:contract"
tx2 = client.send_transaction(account, f"{dapp_name}.{bank_contract_name}.set_authority", {"_controller": controller_address}, is_sync=True)
if not tx2:
    print("✗ set_authority failed")
    sys.exit(1)

time.sleep(3)

title_info("test deposit")
tx3 = client.send_transaction(account, f"{dapp_name}.{ens_contract_name}.invoke", {"operation": "deposit", "amount": 1000}, is_sync=True)
if not tx3:
    print("✗ deposit failed")
    sys.exit(1)

time.sleep(5)
state = client.get_contract_state(dapp_name, bank_contract_name, Scope.Address, account.address)
if state:
    balance = state.get('State', {}).get('balance', 0)
    if balance == 1000:
        print("✓ Deposit successful! Balance: 1000")
    else:
        print(f"✗ Expected 1000, got {balance}")
        sys.exit(1)

title_info("test withdraw")
tx4 = client.send_transaction(account, f"{dapp_name}.{ens_contract_name}.invoke", {"operation": "withdraw", "amount": 100}, is_sync=True)
if not tx4:
    print("✗ withdraw failed")
    sys.exit(1)

time.sleep(5)
state = client.get_contract_state(dapp_name, bank_contract_name, Scope.Address, account.address)
if state:
    balance = state.get('State', {}).get('balance', 0)
    if balance == 900:
        print("✓ Withdraw successful! Balance: 900")
    else:
        print(f"✗ Expected 900, got {balance}")
        sys.exit(1)

print("\n✅ All tests passed!")
