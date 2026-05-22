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

Current conclusion:

- SM2 local signing for `tx.send` is not supported by the current Python SDK implementation.
- The supported SM2 submission path is node-side signing through `tx.send_withSK`.

This is not just a convenience difference. The Python SDK's current local SM2 signature output is not compatible with the live node behavior that accepts the working curl request.


## Current User-Facing Status

The SDK now keeps the two transaction submission styles separate:

- `DioxClient.send_transaction(...)` uses the local compose/sign/send path only
- `DioxClient.send_transaction_with_sk(...)` uses `tx.send_withSK`
- `DioxClient.mint_dio(...)` / `DioxClient.transfer(...)` are local-signing helpers
- `DioxClient.mint_dio_with_sk(...)` / `DioxClient.transfer_with_sk(...)` are node-signing helpers

This keeps the two submission styles at the same level:

- local signing: compose -> sign locally -> `tx.send`
- node signing: send raw business inputs + private key -> `tx.send_withSK`


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

Equivalent Python SDK calls for node-side signing also succeed:

```python
client.send_transaction_with_sk(
    private_key=account.sk_b64,
    function="core.coin.mint",
    args={"Amount": "999999999999999999999999999999"},
)
```

The local compose/sign/send path looks like this:

```python
unsigned = client.compose_transaction(
    sender=account.address,
    function="core.coin.mint",
    args={"Amount": "999999999999999999999999999999"},
)
signed = account.sign_diox_transaction(unsigned)
client.send_raw_transaction(signed, sync=False)
```

### Raw path

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
  - kept `send_transaction(...)` on the local-signing path
  - split `mint_dio(...)` / `transfer(...)` into local-signing helpers plus `mint_dio_with_sk(...)` / `transfer_with_sk(...)`
- `tests/sm2_send_with_sk_live_test.py`
  - direct live test for `tx.send_withSK`
- `tests/sm2_live_test.py`
  - live test showing current SM2 behavior
- `tests/sm2_client_path_test.py`
  - regression coverage for local-signing and node-signing paths


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


### 7. Node `tx.send_withSK` performs its own compose/finalize flow

From the investigated node-side source, `tx.send_withSK` does not accept a caller-built raw transaction.

It:

- composes a transaction internally
- finalizes signer data internally
- signs inside node code
- appends PoW inside node code
- then inserts the finished transaction into the txpool

So `tx.send_withSK` success does not prove that Python local raw signing is generating the same bytes as the node.


### 8. Node-side `SM2` uses a different signing implementation family

From the investigated native security library:

- curve: `sm2p256v1`
- signing scheme: `SM2_Sig(SM3)`
- implementation family: native security code using `Botan`

Python local signing currently uses `gmssl.sign_with_sm3(...)`.

So the two sides are not using the same implementation stack.


### 9. Python local SM2 signature failed verification against node-side security code

A fixed Python-generated test vector was created with:

- the same private key
- the same public key fixture
- the same local signing payload
- a signature produced by Python local signing

That signature was then verified against the investigated node-side security implementation.

Result:

- verification failed

This is the strongest confirmed reason that local SM2 signing is currently unsupported.


### 10. The available source tree and the live node behavior are not perfectly aligned

The investigated source tree helped narrow down the signing flow, but it did not fully explain the live behavior of `101.33.210.216:45678`.

Examples of mismatch:

- the live node accepts the curl request for SM2
- the investigated source suggests different default private-key import behavior in one path
- public key / address derivation observations from the investigated native helper path did not line up cleanly with the live node observations

So the source tree was useful for diagnosis, but it was not sufficient to safely implement a byte-perfect local-signing fix for the live node.


## Current Conclusion

The current SDK should treat SM2 local signing as unsupported for `tx.send`.

The concrete reason is:

1. Python local SM2 signing currently relies on `gmssl`.
2. The node-side accepted SM2 path uses a different native implementation family and signing behavior.
3. A Python-generated local SM2 signature failed verification against the investigated node-side security implementation.
4. Therefore the SDK cannot currently guarantee that `sign_diox_transaction(...)` produces a raw transaction accepted by `tx.send`.

So the safe product behavior is:

- use `tx.send_withSK` for SM2
- do not claim that local SM2 signing is supported for `tx.send`


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


## Suggested Future Fix Direction

If local SM2 signing is ever revisited, it should not be re-enabled by guesswork.

A real fix should start from one of these:

1. Use the exact same signing implementation as the live node.
2. Build a tiny local bridge around the same native security library used by the accepted node path.
3. Obtain the exact live-node source version and verify the full raw transaction build path end to end.

Until then, `tx.send_withSK` should be considered the only supported SM2 submission path.


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
- local SM2 signing is truly accepted by `tx.send`
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

- `send_transaction()` is the local-signing API, while `send_transaction_with_sk()` is the node-signing API
- node-side SM2 support is confirmed by the working curl request
- local SM2 signing for `tx.send` is not supported in the current Python SDK
- the immediate technical reason is signature incompatibility between Python local signing and the investigated node-side verification behavior
