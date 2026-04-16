import sys

sys.path.append(".")

from dioxide_python_sdk.client.account import DioxAccount, DioxAccountType
from dioxide_python_sdk.client.dioxclient import DioxClient


class StubDioxClient(DioxClient):
    def __init__(self):
        super().__init__(url="http://127.0.0.1:1/api", ws_url="ws://127.0.0.1:1/api")
        self.last_sender = None
        self.last_function = None
        self.last_args = None
        self.last_signed_txn = None
        self.last_private_key = None
        self.last_sync = None

    def compose_transaction(
        self,
        sender,
        function,
        args,
        tokens=None,
        isn=None,
        is_delegatee=False,
        gas_price=None,
        gas_limit=None,
    ):
        self.last_sender = sender
        self.last_function = function
        self.last_args = args
        return b"\x01\x02unsigned_tx"

    def send_raw_transaction(self, signed_txn, sync=False, timeout=60):
        self.last_signed_txn = signed_txn
        return "fake_tx_hash"

    def send_transaction_with_sk(self, private_key, function, args, sync=False, timeout=60):
        self.last_private_key = private_key
        self.last_function = function
        self.last_args = args
        self.last_sync = sync
        return "fake_tx_hash_with_sk"


test_sm2_json = {
    "PrivateKey": "+OfM+tj9R8I/BnIjCvc+JAdl0ADy1vAkbu0n2KINwzw=",
    "PublicKey": "AX1hRvLswVwarsbSDiQHzxmSGwR95G4DPfjnLP2oAtDr3kNsJ7X7Q5l5yhnWg/5hTe30O/CZRIbOvv94y3cmvQ==",
    "Address": "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2",
    "AddressType": "SM2",
}


def assert_signed_payload(client, account):
    assert client.last_signed_txn is not None
    sid = account.account_type.value.to_bytes(1, byteorder="little")
    header = b"\x01\x02unsigned_tx" + sid + account.pk_bytes
    assert client.last_signed_txn.startswith(header)
    sig = client.last_signed_txn[len(header):len(header) + 64]
    assert len(sig) == 64
    assert account.verify(sig, header) is True
    pow_part = client.last_signed_txn[len(header) + 64:]
    assert len(pow_part) % 4 == 0


account = DioxAccount.from_json(test_sm2_json, type=DioxAccountType.SM2)
assert account is not None and account.is_valid()

client = StubDioxClient()

mint_tx = client.mint_dio(account, amount=123, sync=False, timeout=1)
assert mint_tx == "fake_tx_hash"
assert client.last_sender == "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2"
assert client.last_function == "core.coin.mint"
assert client.last_args == {"Amount": "123"}
assert_signed_payload(client, account)

mint_with_sk_tx = client.mint_dio_with_sk(account, amount=456, sync=False, timeout=1)
assert mint_with_sk_tx == "fake_tx_hash_with_sk"
assert client.last_private_key == account.sk_b64
assert client.last_function == "core.coin.mint"
assert client.last_args == {"Amount": "456"}
assert client.last_sync is False

proof_tx = client.send_transaction(
    user=account,
    function="silas.ProofOfExistence.new",
    args={"key": "KEY_demo", "content": "CONTENT_demo"},
    is_sync=False,
    timeout=1,
)
assert proof_tx == "fake_tx_hash"
assert client.last_sender == "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2"
assert client.last_function == "silas.ProofOfExistence.new"
assert client.last_args == {"key": "KEY_demo", "content": "CONTENT_demo"}
assert_signed_payload(client, account)

transfer_tx = client.transfer(
    sender=account,
    receiver="receiver_addr:sm2",
    amount=789,
    sync=False,
    timeout=1,
)
assert transfer_tx == "fake_tx_hash"
assert client.last_sender == "zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2"
assert client.last_function == "core.wallet.transfer"
assert client.last_args == {"To": "receiver_addr:sm2", "Amount": "789", "TokenId": "DIO"}
assert_signed_payload(client, account)

transfer_with_sk_tx = client.transfer_with_sk(
    sender=account,
    receiver="receiver_addr:sm2",
    amount=790,
    sync=False,
    timeout=1,
)
assert transfer_with_sk_tx == "fake_tx_hash_with_sk"
assert client.last_private_key == account.sk_b64
assert client.last_function == "core.wallet.transfer"
assert client.last_args == {"To": "receiver_addr:sm2", "Amount": "790", "TokenId": "DIO"}
assert client.last_sync is False
