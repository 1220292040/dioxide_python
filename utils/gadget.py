import hashlib,json

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(f"exception: {e}")
    return wrapper

# pow
class PowDifficulty:
    def __init__(self):
        self._TargetNum = 0
        self._NonZeroBytes = 0

    def set(self, denominator):
        num = 0x8000000000000000 // denominator
        shift = 64 - num.bit_length()
        num <<= shift
        
        exp = 32 * 8 - 63 - shift
        bytes_needed = exp // 8
        residue = exp % 8
        if residue:
            bytes_needed += 1
            num >>= (8 - residue)

        self._TargetNum = num >> 32
        self._NonZeroBytes = bytes_needed + 8  # ULONGLONG size
    
    def is_fullfiled(self,val):
        if self._TargetNum <= int.from_bytes(val[self._NonZeroBytes-4:self._NonZeroBytes],'little'):
            return False
        p = self._NonZeroBytes
        while p < 32:
            if val[p] > 0:
                return False
            p += 1
        return True


def get_pow_difficulty(tx_size):
    pow_diff = PowDifficulty()
    denominator = (1000 + tx_size * (2 * 10 + 100)) // 3
    pow_diff.set(denominator)
    return pow_diff

def calculate_txn_pow(tx):
    pow_data = hashlib.sha512(tx).digest()[0:-4]
    nonces = [0] * 3
    diff = get_pow_difficulty(len(tx)+12)

    nonce = 0
    for i in range(3):
        while True:
            nonce_bytes = nonce.to_bytes(4, byteorder='little')
            hash_result = hashlib.sha256(pow_data + nonce_bytes).digest()
            if diff.is_fullfiled(hash_result):
                nonces[i] = nonce
                break
            nonce += 1
        nonce += 1

    return nonces


def get_subscribe_message(topic: str):
    if topic == "consensus_header":
        return json.dumps({"req": "subscribe.master_commit_head"})
    elif topic == "transaction_block":
        return json.dumps({"req": "subscribe.block_commit_on_head"})
    elif topic == "transaction":
        return json.dumps({"req": "subscribe.txn_confirm_on_head"})
    elif topic == "state":
        return json.dumps({"req": "subscribe.state_update"})
    elif topic == "relays":
        return json.dumps({"req": "subscribe.txn_emit_on_head"})
    else:
        raise ValueError("Invalid topic type")