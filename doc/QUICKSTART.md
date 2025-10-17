# Quick Start Guide

Get started with Dioxide Python SDK.

## Prerequisites

- **Python 3.9 or higher**
- **Git**
- **Running Dioxide node** (for testing functionality)

Check your Python version:
```bash
python3 --version
```

## Setup

This project uses **Poetry** for dependency management.

```bash
# Clone repository
git clone https://github.com/1220292040/dioxide_python.git
cd dioxide_python

# Install dependencies (Poetry will be installed automatically if needed)
make install
```

**What this does:**
1. Installs Poetry if not already installed
2. Creates a virtual environment
3. Installs all project dependencies

**Activate virtual environment:**
```bash
make shell
```

## Verify Setup

Run the demo script to verify everything is working:

```bash
make demo
```

Expected output:
- Node connection successful
- Account creation
- Token minting
- DApp creation
- Contract deployment

## Quick Start Tutorial

### Step 1: Connect to Node

```python
from dioxide_python_sdk.client.dioxclient import DioxClient

# Create client instance
client = DioxClient()

# Check connection
overview = client.get_overview()
print(f"Connected to: {overview['VesionName']}")
print(f"Block height: {overview['HeadHeight']}")
```

### Step 2: Create Account

**Generate New Account:**

```python
from dioxide_python_sdk.client.account import DioxAccount

# Generate new key pair
account = DioxAccount.generate_key_pair()
print(f"Address: {account.address}")
```

**Import Existing Account:**

```python
# From base64 private key
pk = "WTKi+W99TEEt153Zt8isUznwXqYkA0aVWEbd7edk6As="
account = DioxAccount.from_key(pk)
```

### Step 3: Send Transactions

**Mint Tokens:**

```python
# Mint 1000 DIO tokens
tx_hash = client.mint_dio(account, 10**18)
print(f"Mint transaction: {tx_hash}")
```

**Transfer Tokens:**

```python
# Transfer 100 DIO to another address
receiver = "receiver_address_here"
tx_hash = client.transfer(account, receiver, 100)
print(f"Transfer transaction: {tx_hash}")
```

### Step 4: Work with DApps

**Create DApp:**

```python
import time

# Create DApp with unique name (4-8 characters)
dapp_name = f"Dapp{str(int(time.time()))[-2:]}"
tx_hash, ok = client.create_dapp(account, dapp_name, deposit=10**12)

if ok:
    print(f"DApp created: {dapp_name}")
```

**Deploy Contract:**

```python
# Deploy single contract
tx_hash = client.deploy_contract(
    dapp_name=dapp_name,
    delegator=account,
    file_path="./contract.gcl",
    construct_args={"_owner": account.address}
)
```

**Get Contract Info:**

```python
# Query contract information
contract_info = client.get_contract_info(dapp_name, "ContractName")
print(f"Contract ID: {contract_info['ContractID']}")
```

### Step 5: Invoke Contract Functions

```python
from dioxide_python_sdk.client.contract import Scope

# Call contract function
tx_hash = client.send_transaction(
    user=account,
    function=f"{dapp_name}.ContractName.function_name",
    args={"param1": 100, "param2": "value"},
    is_sync=True
)

# Query contract state
state = client.get_contract_state(
    dapp_name=dapp_name,
    contract_name="ContractName",
    scope=Scope.Address,
    key=account.address
)
print(f"Contract state: {state}")
```

### Step 6: Get Transaction Events

```python
# Get events emitted by transaction
events = client.get_events_by_transaction(tx_hash)
for event in events:
    print(f"Event: {event.Target}")
    print(f"Data: {event.Input}")
```

## Configuration

The SDK connects to a Dioxide node. Default configuration is in:

`dioxide_python_sdk/config/client_config.py`

```python
class Config:
    rpc_url = "http://127.0.0.1:45678/api"      # HTTP RPC endpoint
    ws_rpc = "ws://127.0.0.1:45678/api"         # WebSocket endpoint
    log_dir = "logs"                            # Log directory
    default_thread_nums = 32                    # Thread pool size
```

**To change the node address:**
1. Edit `client_config.py`
2. Update `rpc_url` and `ws_rpc`
3. Restart your application

## Common Operations

### Check Account Balance

```python
# Query account state
isn = client.get_isn(account.address)
# ISN > 0 means account exists on chain
```

### Wait for Transaction Confirmation

```python
# Send transaction and wait
tx_hash = client.send_transaction(
    user=account,
    function="some.function",
    args={},
    is_sync=True,
    timeout=60
)
```

### Query Chain Data

```python
# Get latest block number
block_num = client.get_block_number()
print(f"Current block: {block_num}")

# Get block by height
block = client.get_transaction_block_by_height(shard_index=1, height=100)

# Query transaction by hash
tx = client.get_transaction("tx_hash_here")
```

## Troubleshooting

### Poetry not found

If `make install` fails with "Poetry not found":

```bash
make install-poetry
```

### Module not found errors

If you see `ModuleNotFoundError`:

```bash
# Clean and reinstall
make clean
make install
```

### Cannot connect to node

If `demo.py` fails with connection errors:

**1. Check if node is running:**
```bash
netstat -tuln | grep 45678
```

**2. Verify node URL in config:**
- Open `dioxide_python_sdk/config/client_config.py`
- Check `rpc_url` matches your node address

**3. Test node manually:**
```bash
curl http://127.0.0.1:45678/api
```

### Import errors after updating code

```bash
# Deactivate and reactivate environment
exit  # if in make shell
make shell
```

## Tips

1. **Account must have balance** before sending transactions
2. **DApp names** must be 4-8 characters (alphanumeric and underscore)
3. **Use `is_sync=True`** to wait for transaction confirmation
4. **Check node connection** before operations
5. **Handle exceptions** gracefully for production code

## Complete Example

See [demo.py](../demo.py) for a complete working example that demonstrates:
- Node connection
- Account creation
- Token minting
- DApp creation
- Contract deployment
- Contract invocation
- Event querying

Run it with:
```bash
make demo
```

## Next Steps

- Explore [API Reference](API_REFERENCE.md) for all available methods
- Run tests: `make test`
- View all commands: `make help`

## Dependencies

All dependencies are managed by Poetry in `pyproject.toml`:

- `ed25519==1.5` - Ed25519 signature algorithm
- `krock32==0.1.1` - Krock32 encoding
- `crc32c==2.7.post1` - CRC32C checksum
- `python-box==7.2.0` - Box container for dict access
- `requests==2.32.3` - HTTP client library
- `websockets==11.0.3` - WebSocket client support
- `setuptools==75.6.0` - Build and packaging tools

View installed dependencies: `make show-deps`
