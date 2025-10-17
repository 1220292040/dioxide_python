import hashlib,json
from ..client.types import SubscribeTopic
import sys
from .serializer import serialize, deserialize

try:
    import krock32
    KROCK32_AVAILABLE = True
except ImportError:
    KROCK32_AVAILABLE = False
    print("Warning: krock32 module not available, some encoding features may be limited")

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


def get_ttl_from_signed_txn(tx):
    ttl_sc_tsc = int.from_bytes(tx[12:14],'little')
    return 1 + (ttl_sc_tsc & 0x01ff)

def get_pow_difficulty(tx_size,ttl=30):
    pow_diff = PowDifficulty()
    denominator = (1000 + tx_size * (ttl * 10 + 100)) // 3
    pow_diff.set(denominator)
    return pow_diff

def calculate_txn_pow(tx):
    pow_data = hashlib.sha512(tx).digest()[0:-4]
    nonces = [0] * 3
    diff = get_pow_difficulty(len(tx)+12,get_ttl_from_signed_txn(tx))

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

def get_subscribe_message(topic: SubscribeTopic):
    if topic == SubscribeTopic.CONSENSUS_HEADER:
        return json.dumps({"req": "subscribe.master_commit_head"})
    elif topic == SubscribeTopic.TRANSACTION_BLOCK:
        return json.dumps({"req": "subscribe.block_commit_on_head"})
    elif topic == SubscribeTopic.TRANSACTION:
        return json.dumps({"req": "subscribe.txn_confirm_on_head"})
    elif topic == SubscribeTopic.STATE:
        return json.dumps({"req": "subscribe.state_update"})
    elif topic == SubscribeTopic.RELAYS:
        return json.dumps({"req": "subscribe.txn_emit_on_head"})
    elif topic == SubscribeTopic.FINALIZED_BLOCK_AND_TRANSACTION:
        return json.dumps({"req": "subscribe.block_and_txn_finalize"})
    elif topic == SubscribeTopic.MEMPOOL:
        return json.dumps({"req": "subscribe.mempool_insert"})
    else:
        raise ValueError("Invalid topic type")


def progress_bar(current, total, title="" ,bar_length=50):
    fraction = min(current / total,1)
    arrow = int(fraction * bar_length - 1) * '=' + '>'
    padding = (bar_length - len(arrow)) * ' '
    progress = f'{title}[{arrow}{padding}] {int(fraction*100)}%'
    sys.stdout.write('\r' + progress)
    sys.stdout.flush()

def title_info(msg):
    print("#######################{}################".format(msg))


"""
deserialized_args will parse serialized args by signature type order using the new PREDA serializer
signature: str  => "<type1>:<name1>:<type2>:<name2>,<type3>:<name3>...<typen>:<namen>"
for example , in action1(to,1u32,2u32), parse signature: "address:to,uint32:a,uint32:b"
Now supports all PREDA types including array, map, struct
"""
def deserialized_args(signature: str, sargs: str, offset: bool = False):
    """
    Parse serialized arguments using the new PREDA serializer.
    
    Args:
        signature: Type signature string like "address:to,uint32:a,uint32:b"
        sargs: Hex string of serialized data
        offset: Whether to return offset information (for backward compatibility)
    
    Returns:
        Dictionary with parsed arguments
    """
    ret = {}
    data = bytes.fromhex(sargs)
    current_offset = 0

    # Parse signature more carefully to handle nested types
    params = []
    current_param = ""
    depth = 0

    for char in signature:
        if char == '<':
            depth += 1
        elif char == '>':
            depth -= 1
        elif char == ',' and depth == 0:
            params.append(current_param.strip())
            current_param = ""
            continue
        current_param += char

    if current_param.strip():
        params.append(current_param.strip())

    for idx, param in enumerate(params):
        # Find the last colon to separate type and name
        colon_pos = param.rfind(":")
        if colon_pos != -1:
            type_name = param[:colon_pos].strip()
            name = param[colon_pos+1:].strip()
        else:
            type_name = param.strip()
            name = f"value#{idx}"

        try:
            # Use the new PREDA serializer for all types
            value, current_offset = deserialize(type_name, data, current_offset)
            ret[name] = value

        except Exception as e:
            # Fallback to old parsing for backward compatibility
            print(f"Warning: Failed to parse {type_name} with new serializer: {e}")
            print(f"Falling back to manual parsing for {type_name}")

            # Try manual parsing for unsupported types
            try:
                if type_name in ["uint8","uint16","uint32","uint64","uint128","uint256","uint512"]:
                    bitwidth = int(type_name[4:])//8
                    val = int.from_bytes(data[current_offset:current_offset+bitwidth],byteorder='little',signed=False)
                    current_offset += bitwidth
                    ret[name] = val

                elif type_name in ["int8","int16","int32","int64","int128","int256","int512"]:
                    bitwidth = int(type_name[3:])//8
                    val = int.from_bytes(data[current_offset:current_offset+bitwidth],byteorder='little',signed=True)
                    current_offset += bitwidth
                    ret[name] = val

                elif type_name == "bool":
                    val = data[current_offset] != 0
                    current_offset += 1
                    ret[name] = val

                elif type_name == "hash":
                    bitwidth = 32
                    if KROCK32_AVAILABLE:
                        encoder = krock32.Encoder()
                        encoder.update(data[current_offset:current_offset+bitwidth])
                        val = encoder.finalize().lower()
                    else:
                        # Fallback: return hex string
                        val = data[current_offset:current_offset+bitwidth].hex()
                    current_offset += bitwidth
                    ret[name] = val

                elif type_name == "address":
                    bitwidth = 36
                    if KROCK32_AVAILABLE:
                        encoder = krock32.Encoder()
                        encoder.update(data[current_offset:current_offset+bitwidth])
                        val = encoder.finalize().lower()
                    else:
                        # Fallback: return hex string
                        val = data[current_offset:current_offset+bitwidth].hex()
                    current_offset += bitwidth
                    ret[name] = val

                elif type_name == "string":
                    slen = int.from_bytes(data[current_offset:current_offset+2],byteorder='little',signed=False)
                    current_offset += 2
                    val = str(data[current_offset:current_offset+slen],encoding='utf-8')
                    current_offset += slen
                    ret[name] = val

                elif type_name == "bigint":
                    bitmask = int.from_bytes(data[current_offset:current_offset+1],byteorder='little',signed=False)
                    current_offset += 1
                    sig = False if bitmask & 0x80 > 0 else True
                    nlen = bitmask & 0x7f
                    ret_val = 0
                    base = 2**64
                    for i in range(nlen-1,-1,-1):
                        number = int.from_bytes(data[current_offset+i*8:current_offset+(i+1)*8],byteorder='little',signed=False)
                        ret_val = ret_val * base + number
                    current_offset += nlen*8
                    if sig is False:
                        ret_val = -ret_val
                    ret[name] = ret_val

                elif type_name == "token":
                    ret_val = {}
                    pos = current_offset+8
                    for i in range(current_offset,current_offset+8):
                        if data[i] == 0:
                            pos = i
                            break
                    symbol = str(data[current_offset:pos],encoding="utf-8")
                    current_offset += 8
                    ret_val[symbol], current_offset = deserialize("bigint", data, current_offset)
                    ret[name] = ret_val

                else:
                    print(f"Warning: Unsupported type {type_name}, skipping")
                    ret[name] = None

            except Exception as fallback_error:
                print(f"Error in fallback parsing for {type_name}: {fallback_error}")
                ret[name] = None

    if offset:
        return ret, current_offset
    return ret