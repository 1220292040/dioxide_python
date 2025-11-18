import sys
sys.path.append('.')

from dioxide_python_sdk.client.dioxclient import DioxClient

# 初始化客户端，使用示例中的服务器地址
client = DioxClient(url="http://139.196.213.90:62222/api")

# 测试查询合约源代码
dapp_name = "Dapp80"
contract_name = "Bank"

try:
    # 调用 get_source_code 方法
    source_code = client.get_source_code(dapp_name, contract_name)
    print("Contract source code:")
    print(source_code)
except Exception as e:
    print(f"Error: {e}")

