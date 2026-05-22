import os
import sys

sys.path.append(".")

from dioxide_python_sdk.client.dioxclient import DioxClient


RPC_URL = os.getenv("DIOX_RPC_URL", "http://101.33.210.216:45678/api")
PRIVATE_KEY = os.getenv("DIOX_SM2_PRIVATE_KEY", "+OfM+tj9R8I/BnIjCvc+JAdl0ADy1vAkbu0n2KINwzw=")
FUNCTION = os.getenv("DIOX_FUNCTION", "core.coin.mint")
AMOUNT = os.getenv("DIOX_MINT_AMOUNT", "999999999999999999999999999999")


def main():
    client = DioxClient(url=RPC_URL)
    tx_hash = client.send_transaction_with_sk(
        private_key=PRIVATE_KEY,
        function=FUNCTION,
        args={"Amount": AMOUNT},
        sync=False,
    )
    print("rpc:", RPC_URL)
    print("function:", FUNCTION)
    print("amount:", AMOUNT)
    print("tx_hash:", tx_hash)


if __name__ == "__main__":
    main()
