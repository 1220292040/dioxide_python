import base64
import ed25519
import crc32c # type: ignore
import krock32
from enum import Enum
import re

class DioxAccountType(Enum):
    ED25519 = 0
    ETHEREUM = 1
    SM2 = 2
    END = 3

class DioxAddressType(Enum):
    DEFAULT = 0
    NAME = 1
    DAPP = 2
    TOKEN = 3
    DELEGATEE_OFFSET = 8

#--------------------------------------------------------------------------------
class DioxAddress:
    __address = None
    __type = DioxAddressType.DEFAULT

    def __init__(self,addr,type=DioxAddressType.DEFAULT):
        self.__address = addr
        self.__type = type

    def __str__(self):
        return "{}".format(self.address)

    def is_delegatee_name_valid(self,name:str):
        name_len_max = 0
        name_len_min = 0
        char_set = r''
        if self.__type == DioxAddressType.DAPP:
            name_len_min = 3
            name_len_max = 8
            char_set = r'[a-z|A-Z|\d|_]+'
        elif self.__type == DioxAddressType.TOKEN:
            name_len_min = 3
            name_len_max = 8
            char_set = r'[A-Z|\d|-|#]+'
        elif self.__type == DioxAddressType.NAME:
            name_len_min = 3
            name_len_max = 32
            char_set = r'[\w\d|_|-|!|#|$|@|&|^|*|(|)|\[|\]|{|}|<|>|,|;|?|~]+'
        else:
            return False
        if len(name)>name_len_max or len(name)<name_len_min or re.fullmatch(char_set,name) is None:
            return False
        return True

    def set_delegatee_from_string(self,s:str):
        if self.is_delegatee_name_valid(s) is True:
            addr = s.ljust(32,'\x00').encode()
            sid = DioxAddressType.DELEGATEE_OFFSET.value + self.__type.value
            crc = sid | (0xfffffff0 & crc32c.crc32c(addr, sid))
            self.__address = addr + crc.to_bytes(4, 'little')
            return True
        else:
            return False
        
    @property
    def address(self):
        if self.__type == DioxAddressType.DEFAULT:
            encoder = krock32.Encoder()
            encoder.update(self.__address)
            return encoder.finalize().lower()
        else:
            valid = 0
            while valid<32:
                if self.__address[valid] == 0:
                    break
                valid += 1
            addr = self.__address[0:valid]
            return bytes(addr).decode() + ":" + self.__type.name.lower()
    
    @address.setter
    def address(self,address):
        self.__address = address

    @property
    def type(self):
        return self.__type
    
    @address.setter
    def type(self,type):
        self.__type = type

#--------------------------------------------------------------------------------

class DioxAccount:
    __private_key = None
    __public_key = None
    __address = None
    __account_type:DioxAccountType

    def __init__(self,sk,pk,addr,type):
        self.__private_key = sk
        self.__public_key = pk
        self.__address = addr
        self.__account_type = type

    def __str__(self):
        s = '"PrivateKey":{},"PublicKey":{},"Address":{},"AddressType":{}'.format(self.sk_b64,self.pk_b64,self.address,self.account_type.name)
        return "{"+s+"}"


    #TODO support other type of key
    @staticmethod
    def from_key(key,type=DioxAccountType.ED25519):
        try:
            if type == DioxAccountType.ED25519:
                sk_bytes = base64.b64decode(key)[0:32]
                sk = ed25519.SigningKey(sk_s=sk_bytes)
                vk = sk.get_verifying_key()
                crc = 3 | (0xfffffff0 & crc32c.crc32c(vk.vk_s, 3))
                address = vk.vk_s + crc.to_bytes(4, 'little')
                return DioxAccount(sk.sk_s,vk.vk_s,address,type)
            else:
                return None
        except:
            return None
        
    #TODO support other type of key
    @staticmethod
    def from_json(json,type=DioxAccountType.ED25519):
        try:
            sk = None
            pk = None
            addr = None
            if type == DioxAccountType.ED25519:
                if json["PrivateKey"] is not None:
                    sk = base64.b64decode(json["PrivateKey"])
                if json["PublicKey"] is not None:
                    pk = base64.b64decode(json["PublicKey"])
                if json["Address"] is not None:
                    decoder = krock32.Decoder()
                    decoder.update(str(json["Address"]).split(":")[0])
                    addr = decoder.finalize()
                account = DioxAccount(sk,pk,addr,DioxAccountType.ED25519)
                return account if account.is_valid() else None
            else:
                None
        except:
            return None

    #TODO support other type of key
    @staticmethod
    def generate_key_pair(account_type=DioxAccountType.ED25519):
        try:
            if account_type == DioxAccountType.ED25519:
                sk, pk = ed25519.create_keypair()
                crc = 3 | (0xfffffff0 & crc32c.crc32c(pk.vk_s, 3))
                address = pk.vk_s + crc.to_bytes(4, 'little')
                return DioxAccount(sk.sk_s,pk.vk_s,address,DioxAccountType.ED25519)
            else:
                return None
        except:
            return None

    @property
    def sk_b64(self):
        return base64.b64encode(self.sk_bytes).decode("utf-8")
    
    @property
    def pk_b64(self):
        return base64.b64encode(self.pk_bytes).decode("utf-8")

    @property
    def sk_bytes(self):
        return self.__private_key
    
    @sk_bytes.setter
    def sk_bytes(self,sk):
        self.__private_key = sk

    @property
    def pk_bytes(self):
        return self.__public_key

    @pk_bytes.setter
    def pk_bytes(self,pk):
        self.__public_key = pk

    @property
    def address_bytes(self):
        return self.__address

    @property
    def address(self):
        return DioxAddress(self.__address).address
    
    @address.setter
    def address(self,address):
        self.__address = address

    @property
    def account_type(self) -> DioxAccountType:
        return self.__account_type

    @account_type.setter
    def account_type(self,type):
        self.__account_type = type

    def is_valid(self):
        return len(self.sk_bytes) == 64 and \
               len(self.pk_bytes) == 32 and \
               len(self.address_bytes) == 36 and \
               self.account_type.value < DioxAccountType.END.value

    def jsonify(self):
        ret = {}
        ret.update({"PrivateKey":self.sk_b64})
        ret.update({"PublicKey":self.pk_b64})
        ret.update({"Address":self.address})
        ret.update({"AddressType":self.account_type.name})
        return ret

    def sign(self,msg):
        try:
            sk = ed25519.SigningKey(sk_s=self.__private_key)
            sig = sk.sign(msg)
        except:
            return None
        return sig

    def verify(self,sig,msg):
        try:
            pk = ed25519.VerifyingKey(vk_s=self.__public_key)
            pk.verify(sig,msg)
        except:
            return False
        return True
