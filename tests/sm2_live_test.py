import os
import sys

sys.path.append(".")

from dioxide_python_sdk.client.account import DioxAccount, DioxAccountType
from dioxide_python_sdk.client.dioxclient import DioxClient, DioxError


RPC_URL = os.getenv("DIOX_RPC_URL", "http://101.33.210.216:45678/api")
PRIVATE_KEY = os.getenv("DIOX_SM2_PRIVATE_KEY", "+OfM+tj9R8I/BnIjCvc+JAdl0ADy1vAkbu0n2KINwzw=")
PUBLIC_KEY = os.getenv(
    "DIOX_SM2_PUBLIC_KEY",
    "AX1hRvLswVwarsbSDiQHzxmSGwR95G4DPfjnLP2oAtDr3kNsJ7X7Q5l5yhnWg/5hTe30O/CZRIbOvv94y3cmvQ==",
)
ADDRESS = os.getenv(
    "DIOX_SM2_ADDRESS",
    "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2",
)
AMOUNT = os.getenv("DIOX_MINT_AMOUNT", "999999999999999999999999999999")
SEND_TX = os.getenv("DIOX_SEND_LIVE_TX", "").lower() in {"1", "true", "yes"}
USE_NODE_SIGNING = os.getenv("DIOX_USE_NODE_SIGNING", "1").lower() in {"1", "true", "yes"}


def main():
    client = DioxClient(url=RPC_URL)
    account = DioxAccount.from_json(
        {
            "PrivateKey": PRIVATE_KEY,
            "PublicKey": PUBLIC_KEY,
            "Address": ADDRESS,
            "AddressType": "SM2",
        },
        type=DioxAccountType.SM2,
    )
    assert account is not None and account.is_valid(), "invalid SM2 account fixture"

    print("rpc:", RPC_URL)
    overview = client.get_overview()
    print("network:", overview.get("VersionName", "unknown"))
    print("head_height:", overview.get("HeadHeight", "unknown"))
    print("address:", account.address)
    print("isn:", client.get_isn(account.address))
    print("function:", "core.coin.mint")
    print("amount:", AMOUNT)
    print("use_node_signing:", USE_NODE_SIGNING)

    unsigned_txn = client.compose_transaction(
        sender=account.address,
        function="core.coin.mint",
        args={"Amount": AMOUNT},
    )
    signed_txn = account.sign_diox_transaction(unsigned_txn)
    print("unsigned_txn_bytes:", len(unsigned_txn))
    print("signed_txn_bytes:", len(signed_txn))

    if not SEND_TX:
        print("broadcast:", "skipped")
        print("hint:", "set DIOX_SEND_LIVE_TX=1 to actually submit the transaction")
        return

    try:
        if USE_NODE_SIGNING:
            tx_hash = client.mint_dio_with_sk(
                user=account,
                amount=AMOUNT,
                sync=False,
            )
        else:
            tx_hash = client.send_raw_transaction(signed_txn, sync=False)
    except DioxError as exc:
        print("broadcast:", "failed")
        print("error_code:", exc.code)
        print("error_message:", exc.message)
        print("hint:", "try DIOX_USE_NODE_SIGNING=1 for mint_dio_with_sk on the node")
        if exc.code == 10011:
            return
        raise

    print("broadcast:", "submitted")
    print("tx_hash:", tx_hash)


if __name__ == "__main__":
    main()
