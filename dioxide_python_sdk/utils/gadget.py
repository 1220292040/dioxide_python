import hashlib,json
from ..client.types import SubscribeTopic
import struct
import krock32

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
    else:
        raise ValueError("Invalid topic type")
    

def title_info(msg):
    print("#######################{}################".format(msg))


"""
parse_serialized_args will parse serialized args by signature type order
signature: str  => "<name1>:<type1>,<name2>:<type2>,<name3>:<type3>...<namen>:<typen>"
for example , in action1(to,1u32,2u32), parse signature: "to:address,a:uint32,b:uint32"
"""
def parse_serialized_args(sigature:str,sargs):
    def parse_uint(type,data,cur):
        bitwidth = int(type[4:])//8
        val = struct.unpack('<I',data[cur:cur+bitwidth])[0]
        print(f"debug: bitwidth => {bitwidth}, {name}:{val}")
        cur += bitwidth
        return val,cur
    
    def parse_int(type,data,cur):
        bitwidth = int(type[3:])//8
        val = struct.unpack('<i',data[cur:cur+bitwidth])[0]
        print(f"debug: bitwidth => {bitwidth}, {name}:{val}")
        cur += bitwidth
        return val,cur

    def parse_float(type,data,cur):
        exp_bitwith = 8
        man_bitwith = int(type[5:])//8-8
        sign_bitwith = 4
        exp = int.from_bytes(data[cur:cur+exp_bitwith],byteorder='little',signed=True)
        cur += exp_bitwith

        pos = 0
        for i in range(cur,cur+man_bitwith):
            if data[i] == 0:
                exp+=8
            else:
                pos = i
                break
        man = int.from_bytes(data[pos:cur+man_bitwith],byteorder='little',signed=False)
        val = (2**exp) * man 
        cur += man_bitwith

        sign = int.from_bytes(data[cur:cur+sign_bitwith],byteorder='little',signed=False) & 128
        cur += sign_bitwith
        
        if sign is True:
            return val,cur
        else:
            return -val,cur

    def parse_bool(data,cur):
        bitwidth = 1
        val = data[cur]
        cur += bitwidth
        if val != 0:
            return "true",cur
        else:
            return "false",cur
   
    def parse_hash(data,cur):
        bitwidth = 32
        encoder = krock32.Encoder()
        encoder.update(data[cur:cur+bitwidth])
        val = encoder.finalize().lower()
        cur += bitwidth
        return val,cur

    def parse_address(data,cur):
        bitwidth = 36
        encoder = krock32.Encoder()
        encoder.update(data[cur:cur+bitwidth])
        val = encoder.finalize().lower()
        cur += bitwidth
        return val+":ed25519",cur

    def parse_string(data,cur):
        slen = int.from_bytes(data[cur:cur+2],byteorder='little',signed=False)
        cur += 2
        val = str(data[cur:cur+slen],encoding='utf-8')
        cur += slen
        return val,cur

    ret = {}
    params = sigature.split(",")
    data = bytes.fromhex(sargs)
    cur = 0
    for param in params:
        pname_and_type = param.split(":")
        type = pname_and_type[0]
        name = pname_and_type[1]
        #fixed-size
        if type in ["uint8","uint16","uint32","uint64","uint128","uint256","uint512"]:
            ret[name],cur = parse_uint(type,data,cur)
            
        elif type in ["int8","int16","int32","int64","int128","int256","int512"]:
            ret[name],cur = parse_int(type,data,cur)

        elif type in ["float256","float512","float1024"]:
            ret[name],cur = parse_float(type,data,cur)

        elif type == "bool":
            ret[name],cur = parse_bool(data,cur)
            
        elif type == "hash":
            ret[name],cur = parse_hash(data,cur)

        elif type == "address":
            ret[name],cur = parse_address(data,cur)
        
        elif type == "string":
            ret[name],cur = parse_string(data,cur)

        else:
            pass
    return ret