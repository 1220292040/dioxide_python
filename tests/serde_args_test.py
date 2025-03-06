import krock32

def parse_serialized_args(sigature:str,sargs,offset=False):
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
        type = pname_and_type[0]
        name = "value#"+str(idx)
        if len(pname_and_type) == 2:
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

        elif type == "bigint":
            ret[name],cur = parse_bigint(data,cur)
        
        elif type == "token":
            ret[name],cur = parse_token(data,cur)

        else:
            pass

        idx += 1
    
    return ret

if __name__ == "__main__":
    test = "e2bc6a2fe6104b24b41b4b6864f1b9c2dc533c12debe0316b0d6eba471ef99115336d582e803000000000000000000000000000000000000000000000000000000000000"
    ret1 = parse_serialized_args("address:to,uint256:amount",test)
    print(ret1)
