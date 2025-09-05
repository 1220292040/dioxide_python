import hashlib,json
from ..client.types import SubscribeTopic
import krock32
import sys

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
deserialized_args will parse serialized args by signature type order
signature: str  => "<type1>:<name1>:<type2>:<name2>,<type3>:<name3>...<typen>:<namen>"
for example , in action1(to,1u32,2u32), parse signature: "address:to,uint32:a,uint32:b"
Warning!: only support fixed-size (int,float,uint,address,hash..) and bigint,token,string, not support array,map,struct
"""
def deserialized_args(sigature:str,sargs,offset=False):
    def parse_uint(type,data,cur):
        bitwidth = int(type[4:])//8
        val = int.from_bytes(data[cur:cur+bitwidth],byteorder='little',signed=False)
        cur += bitwidth
        return val,cur
    
    def parse_int(type,data,cur):
        bitwidth = int(type[3:])//8
        val = int.from_bytes(data[cur:cur+bitwidth],byteorder='little',signed=True)
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
        return val,cur

    def parse_string(data,cur):
        slen = int.from_bytes(data[cur:cur+2],byteorder='little',signed=False)
        cur += 2
        val = str(data[cur:cur+slen],encoding='utf-8')
        cur += slen
        return val,cur

    def parse_bigint(data,cur):
        bitmask = int.from_bytes(data[cur:cur+1],byteorder='little',signed=False)
        cur += 1
        sig = False if bitmask & 0x80 > 0 else True
        nlen = bitmask & 0x7f
        ret = 0
        base = 2**64
        for i in range(nlen-1,-1,-1):
            number = int.from_bytes(data[cur+i*8:cur+(i+1)*8],byteorder='little',signed=False)
            ret = ret * base + number
        cur += nlen*8
        if sig is False:
            ret = -ret
        return ret,cur

    def parse_token(data,cur):
        ret = {}
        pos = cur+8
        for i in range(cur,cur+8):
            if data[i] == 0:
                pos = i
                break
        symbol = str(data[cur:pos],encoding="utf-8")
        cur += 8
        ret[symbol],cur = parse_bigint(data,cur)
        return ret,cur

    def parse_in_type(sig,type):
        start = type.find(sig)
        start += len(sig)
        level = 1
        content = []
        for char in type[start:]:
            if char == '<':
                level += 1
            elif char == '>':
                level -= 1
                if level == 0:
                    return ''.join(content)
            content.append(char)
        return None

    ret = {}
    params = sigature.split(",")
    data = bytes.fromhex(sargs)
    cur = 0
    idx = 0
    for param in params:
        pname_and_type = param.split(":")
        type = pname_and_type[0].strip()
        name = "value#"+str(idx)
        if len(pname_and_type) == 2:
            name = pname_and_type[1].strip()
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

        elif type == "bigint":
            ret[name],cur = parse_bigint(data,cur)
        
        elif type == "token":
            ret[name],cur = parse_token(data,cur)

        else:
            pass

        idx += 1
    
    return ret