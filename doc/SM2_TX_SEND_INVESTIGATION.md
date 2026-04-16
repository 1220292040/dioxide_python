# SM2 `tx.send` Investigation Notes

## Problem Summary

The Python SDK can successfully submit SM2 transactions through RPC method `tx.send_withSK`, but the raw local-signing path:

- `compose_transaction(...)`
- `sign_diox_transaction(...)`
- `send_raw_transaction(...)` -> `tx.send`

still fails with:

```text
(10011, 'insert txpool rejected.')
```

This means the SDK is currently usable for SM2 accounts only by routing through node-side signing (`tx.send_withSK`), not by producing a raw signed transaction locally and sending it with `tx.send`.


## Current User-Facing Status

To keep the SDK usable, `SM2` accounts now default to node-side signing:

- `DioxClient.send_transaction(..., use_node_signing=None)` auto-selects `tx.send_withSK` for `SM2`
- `DioxClient.mint_dio(..., use_node_signing=None)` auto-selects `tx.send_withSK` for `SM2`
- `DioxClient.transfer(..., use_node_signing=None)` auto-selects `tx.send_withSK` for `SM2`

This fixes the practical issue that Python SDK calls should behave like the working curl request.

However, this is a workaround at the SDK routing level, not a true fix for the raw `tx.send` path.


## Reproduction

### Working curl

This succeeds:

```bash
curl --location --request GET 'http://101.33.210.216:45678/api?req=tx.send_withSK' \
--header 'Content-Type: application/json' \
--data '{
  "privatekey":"+OfM+tj9R8I/BnIjCvc+JAdl0ADy1vAkbu0n2KINwzw=",
  "function":"core.coin.mint",
  "args":{
    "Amount":"999999999999999999999999999999"
  }
}'
```

Equivalent Python SDK calls now also succeed:

```python
client.send_transaction_with_sk(
    private_key=account.sk_b64,
    function="core.coin.mint",
    args={"Amount": "999999999999999999999999999999"},
)
```

and

```python
client.mint_dio(
    account,
    "999999999999999999999999999999",
    sync=False,
)
```

for `SM2`, because `send_transaction()` now defaults to node signing.

### Failing raw path

This still fails:

```python
unsigned = client.compose_transaction(
    sender=account.address,
    function="core.coin.mint",
    args={"Amount": "999999999999999999999999999999"},
)
signed = account.sign_diox_transaction(unsigned)
client.send_raw_transaction(signed, sync=False)
```

Error:

```text
(10011, 'insert txpool rejected.')
```


## Files Touched So Far

- `dioxide_python_sdk/client/dioxclient.py`
  - added `send_transaction_with_sk(...)`
  - changed `send_transaction(...)` to auto-use node signing for `SM2`
  - changed `mint_dio(...)` / `transfer(...)` to inherit that behavior
- `tests/sm2_send_with_sk_live_test.py`
  - direct live test for `tx.send_withSK`
- `tests/sm2_live_test.py`
  - live test showing current SM2 behavior
- `tests/sm2_client_path_test.py`
  - regression coverage for default SM2 routing


## What Has Been Verified

### 1. RPC node is not generally rejecting transactions

Initial assumption was wrong.

The node does accept SM2 transactions when using `tx.send_withSK`.

So the problem is specifically:

- local SDK-produced raw signed tx -> `tx.send` fails
- node-side signing path -> `tx.send_withSK` succeeds


### 2. Private key and public key do match

The SM2 public key fixture was verified against the private key using `gmssl`.

So the failure is not caused by a mismatched keypair.


### 3. The raw tx size is plausible

For a short amount like `"9"`:

- unsigned tx length from `tx.compose`: `40`
- signed bundle length with current local logic: `181`

Successful `tx.send_withSK` transactions retrieved from chain also had `Size: 181`.

So this is not simply a total-length mismatch.


### 4. PoW nonce count was tested

The current local implementation appends 3 nonces (`12` bytes).

Tests were done with:

- 1 nonce
- 2 nonces
- 3 nonces

All still failed with `10011`.

So this does not look like a simple “wrong number of PoW nonces” issue.


### 5. Several signing variants were tested and all failed

Tried variants including:

- `sign_with_sm3(payload)`
- `sign(SM3(payload))`
- `sign(SHA256(payload))`
- `sign(SHA512(payload)[:32])`

Also tried several metadata/layout combinations involving:

- `sid + public_key`
- `public_key + sid`
- signing `unsigned`
- signing `unsigned + metadata`
- placing signature before/after metadata

All still failed with `10011`.


### 6. Function aliasing was observed but did not fix the issue

Transactions sent through `tx.send_withSK` for:

- `core.coin.mint`

were later observed on chain as:

- `core.coin.address.mint`

But trying to locally compose/send raw tx with:

- `core.coin.mint`
- `core.coin.address.mint`

still failed in both cases.

So there may be aliasing on the node, but it is not the root cause by itself.


## Current Hypotheses

The remaining likely causes are:

1. The raw signed transaction layout expected by node `tx.send` for `SM2` differs from the SDK's current `sign_diox_transaction(...)` implementation.

2. The signing payload for `SM2` is not the same as:

```text
unsigned_tx + sid + public_key
```

3. The node may use a special SM2 raw transaction packing rule that is not visible from `tx.send_withSK`.

4. The node may be transforming `core.coin.mint` into another invocation form before signing/sending, so the `tx.compose` output used by the SDK is not byte-equivalent to the node's internal unsigned tx.


## Most Relevant Code

### Current local signing implementation

File:

- `dioxide_python_sdk/client/account.py`

Method:

- `sign_diox_transaction(self, txdata)`

Current logic:

```python
sid = self.account_type.value.to_bytes(1, byteorder="little")
sign_payload = txdata + sid + self.__public_key
sig = self.sign(sign_payload)
signed_tx_data = sign_payload + sig
nonces = calculate_txn_pow(signed_tx_data)
for nonce in nonces:
    signed_tx_data = signed_tx_data + nonce.to_bytes(4, 'little')
return signed_tx_data
```

This is the most suspicious place.

### Raw submission path

File:

- `dioxide_python_sdk/client/dioxclient.py`

Methods:

- `send_raw_transaction(...)`
- `send_transaction(...)`
- `send_transaction_with_sk(...)`


## Suggested Next Steps On A Machine With Node Source

The best next step is to inspect the node implementation of:

- `tx.send`
- `tx.send_withSK`
- SM2 transaction verification / signer extraction
- SM2 raw signed transaction decoding

Questions to answer from node source:

1. For `tx.send`, what exact binary layout is expected?
2. What bytes are covered by the SM2 signature?
3. Is `sid` included in signed payload, and where?
4. Is public key embedded in raw tx, and where?
5. How many PoW nonces are expected?
6. Is `tx.compose` output byte-identical to the unsigned tx built inside `tx.send_withSK`?
7. Does `core.coin.mint` get rewritten to `core.coin.address.mint` before signing?


## Useful Validation Target

A real fix should make this succeed:

```python
account = DioxAccount.from_json(sm2_fixture, type=DioxAccountType.SM2)
unsigned = client.compose_transaction(
    sender=account.address,
    function="core.coin.mint",
    args={"Amount": "999999999999999999999999999999"},
)
signed = account.sign_diox_transaction(unsigned)
tx_hash = client.send_raw_transaction(signed, sync=False)
```

Acceptance criteria:

- `tx.send` returns a tx hash
- the transaction is confirmed on chain
- `use_node_signing=False` works for `SM2`
- SDK no longer needs to special-case `SM2` to avoid `tx.send`


## Handy Commands

Current working live tests:

```bash
poetry run python tests/sm2_send_with_sk_live_test.py
```

```bash
DIOX_SEND_LIVE_TX=1 poetry run python tests/sm2_live_test.py
```

Manual repro for failing raw path:

```bash
poetry run python - <<'PY'
import sys
sys.path.append('.')
from dioxide_python_sdk.client.account import DioxAccount, DioxAccountType
from dioxide_python_sdk.client.dioxclient import DioxClient

client = DioxClient(url='http://101.33.210.216:45678/api')
account = DioxAccount.from_json({
    'PrivateKey': '+OfM+tj9R8I/BnIjCvc+JAdl0ADy1vAkbu0n2KINwzw=',
    'PublicKey': 'AX1hRvLswVwarsbSDiQHzxmSGwR95G4DPfjnLP2oAtDr3kNsJ7X7Q5l5yhnWg/5hTe30O/CZRIbOvv94y3cmvQ==',
    'Address': 'zqgx8f30g04qpd2fxxm9e05een3ytjp970vzbjnhctjrf7kj5per84cj34:sm2',
    'AddressType': 'SM2',
}, type=DioxAccountType.SM2)

unsigned = client.compose_transaction(
    sender=account.address,
    function='core.coin.mint',
    args={'Amount': '999999999999999999999999999999'},
)
signed = account.sign_diox_transaction(unsigned)
print(client.send_raw_transaction(signed, sync=False))
PY
```


## Final State At Handoff

At handoff time:

- practical SDK behavior for SM2 is fixed by defaulting to `tx.send_withSK`
- true raw `tx.send` compatibility for SM2 is still unresolved
- root cause is narrowed to SM2 raw transaction packing / signing semantics on the node side
