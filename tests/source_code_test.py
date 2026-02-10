import sys
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient

# Initialize client with example server URL
client = DioxClient(url="http://139.196.213.90:62222/api")

# Test query contract source code
dapp_name = "Dapp80"
contract_name = "Bank"

try:
    # Call get_source_code
    source_code = client.get_source_code(dapp_name, contract_name)
    print("Contract source code:")
    print(source_code)
except Exception as e:
    print(f"Error: {e}")

