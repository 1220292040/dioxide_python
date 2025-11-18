# API Reference

Complete API documentation for Dioxide Python SDK.

## Table of Contents

- [DioxClient](#dioxclient)
  - [Initialization](#initialization)
  - [Chain Queries](#chain-queries)
  - [Transaction Operations](#transaction-operations)
  - [Contract Operations](#contract-operations)
  - [DApp Operations](#dapp-operations)
  - [Token Operations](#token-operations)
  - [Subscription Methods](#subscription-methods)
- [DioxAccount](#dioxaccount)
- [Data Types](#data-types)
- [Enums](#enums)

## DioxClient

Main client for interacting with Dioxide blockchain.

### Initialization

```python
from dioxide_python_sdk.client.dioxclient import DioxClient

client = DioxClient(
    url="http://127.0.0.1:62222/api",  # Optional, default from config
    ws_url="ws://127.0.0.1:62222/api"   # Optional, default from config
)
```

### Chain Queries

#### get_overview()

Get overview information of the blockchain.

```python
overview = client.get_overview()
# Returns: dict with VesionName, HeadHeight, etc.
```

**Returns**: `dict` containing chain information

#### get_block_number()

Get current block height.

```python
height = client.get_block_number()
```

**Returns**: `int` - current block number

#### get_shard_index(scope, scope_key)

Get shard index for a given scope and key.

```python
shard = client.get_shard_index("global", None)
shard = client.get_shard_index("address", "address_here")
```

**Parameters**:
- `scope` (str): Scope type ("global", "shard", "address", "uint256")
- `scope_key`: Scope key (depends on scope type)

**Returns**: `int` - shard index

#### get_isn(address)

Get Incremental Sequence Number (ISN) for an address.

```python
isn = client.get_isn(account.address)
```

**Parameters**:
- `address` (str): Account address

**Returns**: `int` - account's ISN

#### get_consensus_header_by_height(height)

Get consensus header by block height.

```python
header = client.get_consensus_header_by_height(100)
```

**Parameters**:
- `height` (int): Block height

**Returns**: `dict` - consensus header

#### get_consensus_header_by_hash(hash)

Get consensus header by block hash.

```python
header = client.get_consensus_header_by_hash("block_hash")
```

**Parameters**:
- `hash` (str): Block hash

**Returns**: `dict` - consensus header

#### get_transaction_block_by_height(shard_index, height)

Get transaction block by shard and height.

```python
block = client.get_transaction_block_by_height(1, 100)
```

**Parameters**:
- `shard_index` (int): Shard index
- `height` (int): Block height

**Returns**: `dict` - transaction block

#### get_transaction_block_by_hash(shard_index, hash)

Get transaction block by shard and hash.

```python
block = client.get_transaction_block_by_hash(1, "block_hash")
```

**Parameters**:
- `shard_index` (int): Shard index
- `hash` (str): Block hash

**Returns**: `dict` - transaction block

#### get_transaction(hash, shard_index=None)

Get transaction details by hash.

```python
tx = client.get_transaction("tx_hash")
```

**Parameters**:
- `hash` (str): Transaction hash
- `shard_index` (int, optional): Shard index

**Returns**: `dict` - transaction details

### Transaction Operations

#### compose_transaction(sender, function, args, ...)

Compose a transaction without signing.

```python
tx = client.compose_transaction(
    sender=account,
    function="dapp.contract.function",
    args={"param": "value"},
    tokens=[],
    isn=None,
    is_delegatee=False,
    gas_price=None,
    gas_limit=None,
    ttl=None
)
```

**Parameters**:
- `sender` (DioxAccount): Sender account
- `function` (str): Function to call
- `args` (dict): Function arguments
- `tokens` (list, optional): Token transfers
- `isn` (int, optional): ISN (auto-fetched if None)
- `is_delegatee` (bool): Whether transaction is delegated
- `gas_price` (int, optional): Gas price
- `gas_limit` (int, optional): Gas limit
- `ttl` (int, optional): Time to live

**Returns**: `bytes` - unsigned transaction

#### send_transaction(user, function, args, ...)

Send a signed transaction.

```python
tx_hash = client.send_transaction(
    user=account,
    function="dapp.contract.function",
    args={"param": "value"},
    tokens=None,
    isn=None,
    is_delegatee=False,
    gas_price=None,
    gas_limit=None,
    is_sync=False,
    timeout=60
)
```

**Parameters**:
- Same as `compose_transaction`
- `is_sync` (bool): Wait for confirmation
- `timeout` (int): Timeout for sync wait

**Returns**: `str` - transaction hash, or `None` if sync failed

#### send_raw_transaction(signed_txn, sync=False, timeout=60)

Send raw signed transaction bytes.

```python
tx_hash = client.send_raw_transaction(signed_tx, sync=True)
```

**Parameters**:
- `signed_txn` (bytes): Signed transaction
- `sync` (bool): Wait for confirmation
- `timeout` (int): Timeout seconds

**Returns**: `str` - transaction hash

#### mint_dio(user, amount, sync=True, timeout=60)

Mint DIO tokens (testnet only).

```python
tx_hash = client.mint_dio(account, 10**18)
```

**Parameters**:
- `user` (DioxAccount): Account to receive tokens
- `amount` (int): Amount in minimal units
- `sync` (bool): Wait for confirmation
- `timeout` (int): Timeout seconds

**Returns**: `str` - transaction hash

#### transfer(sender, receiver, amount, token="DIO", sync=True, timeout=60)

Transfer tokens between accounts.

```python
tx_hash = client.transfer(sender, receiver_address, 100, token="DIO")
```

**Parameters**:
- `sender` (DioxAccount): Sender account
- `receiver` (str): Receiver address
- `amount` (int): Amount to transfer
- `token` (str): Token symbol
- `sync` (bool): Wait for confirmation
- `timeout` (int): Timeout seconds

**Returns**: `str` - transaction hash

### Contract Operations

#### get_contract_info(dapp_name, contract_name)

Get contract information.

```python
info = client.get_contract_info("MyDapp", "MyContract")
```

**Parameters**:
- `dapp_name` (str): DApp name
- `contract_name` (str): Contract name

**Returns**: `dict` - contract info (ContractID, Code, etc.)

#### get_source_code(dapp_name, contract_name)

Get source code of a deployed contract.

```python
source_code = client.get_source_code("MyDapp", "MyContract")
print(source_code)
```

**Parameters**:
- `dapp_name` (str): DApp name
- `contract_name` (str): Contract name

**Returns**: `str` - contract source code

#### deploy_contract(dapp_name, delegator, file_path=None, source_code=None, construct_args=None, compile_time=None)

Deploy a single contract.

```python
tx_hash = client.deploy_contract(
    dapp_name="MyDapp",
    delegator=account,
    file_path="./contract.gcl",
    construct_args={"_owner": account.address},
    compile_time=20
)
```

**Parameters**:
- `dapp_name` (str): DApp name
- `delegator` (DioxAccount): Account deploying contract
- `file_path` (str, optional): Contract file path
- `source_code` (str, optional): Contract source code
- `construct_args` (dict, optional): Constructor arguments
- `compile_time` (int, optional): Compilation timeout

**Returns**: `str` - deployment transaction hash

#### deploy_contracts(dapp_name, delegator, dir_path=None, suffix=".gcl", construct_args=None, compile_time=None)

Deploy multiple contracts from directory.

```python
tx_hash = client.deploy_contracts(
    dapp_name="MyDapp",
    delegator=account,
    dir_path="./contracts",
    construct_args=[
        {"_owner": account.address},
        None,
        {"_admin": account.address}
    ],
    compile_time=30
)
```

**Parameters**:
- `dapp_name` (str): DApp name
- `delegator` (DioxAccount): Account deploying contracts
- `dir_path` (str): Directory containing contracts
- `suffix` (str): File suffix filter
- `construct_args` (list[dict]): Constructor args for each contract
- `compile_time` (int, optional): Compilation timeout

**Returns**: `str` - deployment transaction hash

**Note**: Contracts are automatically sorted by dependency order.

#### get_contract_state(dapp_name, contract_name, scope, key)

Query contract state.

```python
from dioxide_python_sdk.client.contract import Scope

state = client.get_contract_state(
    dapp_name="MyDapp",
    contract_name="MyContract",
    scope=Scope.Address,
    key=account.address
)
```

**Parameters**:
- `dapp_name` (str): DApp name
- `contract_name` (str): Contract name
- `scope` (Scope): State scope type
- `key`: State key

**Returns**: State value

#### get_events_by_transaction(txhash)

Get events emitted by transaction.

```python
events = client.get_events_by_transaction("tx_hash")
for event in events:
    print(event.Target, event.Input)
```

**Parameters**:
- `txhash` (str): Transaction hash

**Returns**: `list` - event objects

### DApp Operations

#### create_dapp(user, dapp_name, deposit_amount, sync=True, timeout=60)

Create a new DApp.

```python
tx_hash, ok = client.create_dapp(account, "MyDapp", 10**12)
```

**Parameters**:
- `user` (DioxAccount): Creator account
- `dapp_name` (str): DApp name (4-8 chars)
- `deposit_amount` (int): Deposit amount
- `sync` (bool): Wait for confirmation
- `timeout` (int): Timeout seconds

**Returns**: `tuple(str, bool)` - (transaction hash, success)

#### get_dapp_info(dapp_name)

Get DApp information.

```python
info = client.get_dapp_info("MyDapp")
```

**Parameters**:
- `dapp_name` (str): DApp name

**Returns**: `dict` - DApp info

### Token Operations

#### create_token(user, symbol, initial_supply, deposit, decimals, ...)

Create a new token.

```python
tx_hash = client.create_token(
    user=account,
    symbol="MTK",
    initial_supply=1000000,
    deposit=10**12,
    decimals=18
)
```

**Parameters**:
- `user` (DioxAccount): Creator account
- `symbol` (str): Token symbol
- `initial_supply` (int): Initial token supply
- `deposit` (int): Deposit amount
- `decimals` (int): Token decimals
- `cid` (int, optional): Contract ID
- `minter_flag` (int): Minter flag
- `token_flag` (int): Token flag
- `sync` (bool): Wait for confirmation
- `timeout` (int): Timeout seconds

**Returns**: `str` - transaction hash

#### get_token_info(token_symbol)

Get token information.

```python
info = client.get_token_info("DIO")
```

**Parameters**:
- `token_symbol` (str): Token symbol

**Returns**: `dict` - token info

### Subscription Methods

#### subscribe(topic, handler=None, filter=None)

Subscribe to blockchain events via WebSocket.

```python
from dioxide_python_sdk.client.types import SubscribeTopic

thread_id = client.subscribe(
    topic=SubscribeTopic.State,
    handler=my_handler_function,
    filter=my_filter_function
)
```

**Parameters**:
- `topic` (SubscribeTopic): Topic to subscribe
- `handler` (callable): Event handler function
- `filter` (callable, optional): Event filter function

**Returns**: `int` - subscription thread ID

#### subscribe_state_with_dapp(dapp_name, handler=None)

Subscribe to state updates for a specific DApp.

```python
thread_id = client.subscribe_state_with_dapp("MyDapp", my_handler)
```

#### subscribe_state_with_contract(dapp_contract_name, handler=None)

Subscribe to state updates for a specific contract.

```python
thread_id = client.subscribe_state_with_contract("MyDapp.MyContract", my_handler)
```

#### unsubscribe(thread_id)

Unsubscribe from events.

```python
client.unsubscribe(thread_id)
```

**Parameters**:
- `thread_id` (int): Subscription thread ID

### Utility Methods

#### is_tx_confirmed(tx)

Check if transaction is confirmed.

```python
confirmed = client.is_tx_confirmed(tx_hash)
```

#### is_tx_success(tx)

Check if transaction succeeded.

```python
success = client.is_tx_success(tx_hash)
```

#### wait_for_transaction_confirmed(tx_hash, timeout)

Wait for transaction confirmation.

```python
result = client.wait_for_transaction_confirmed(tx_hash, 60)
```

## DioxAccount

Account management class.

### Methods

#### generate_key_pair()

Generate new Ed25519 key pair.

```python
account = DioxAccount.generate_key_pair()
```

**Returns**: `DioxAccount` instance

#### from_key(private_key)

Create account from private key.

```python
account = DioxAccount.from_key("base64_private_key")
```

**Parameters**:
- `private_key` (str): Base64 encoded private key

**Returns**: `DioxAccount` instance

### Properties

- `address` (str): Account address
- `public_key` (bytes): Public key
- `private_key` (bytes): Private key

## Data Types

### SubscribeTopic

```python
class SubscribeTopic:
    State = "State"
    Transaction = "Transaction"
    ExternalRelay = "ExternalRelay"
```

### Scope

```python
class Scope:
    Global = "global"
    Address = "address"
    Uint256 = "uint256"
```

## Enums

### DioxAddressType

Address type enumeration.

```python
class DioxAddressType:
    Ed25519 = "ed25519"
    Contract = "contract"
```

## Error Handling

```python
from dioxide_python_sdk.client.dioxclient import DioxError

try:
    result = client.some_operation()
except DioxError as e:
    print(f"Error code: {e.code}")
    print(f"Error message: {e.message}")
```

## See Also

- [Quick Start Guide](QUICKSTART.md) - Complete setup and tutorial
