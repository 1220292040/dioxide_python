from enum import Enum
from .types import EngineID

Scope = Enum('Scope',[('Global',0),('Shard',1),('Address',2)])

CORE_CONTRACT_SCOPE_BITSHIFT = 6
CORE_CONTRACT_GLOBAL_BEGIN = Scope.Global.value<<CORE_CONTRACT_SCOPE_BITSHIFT
CORE_CONTRACT_SHARD_BEGIN = Scope.Shard.value<<CORE_CONTRACT_SCOPE_BITSHIFT
CORE_CONTRACT_ADDRESS_BEGIN = Scope.Address.value<<CORE_CONTRACT_SCOPE_BITSHIFT

CORE_CONTRACT_COIN_GLOBAL = CORE_CONTRACT_GLOBAL_BEGIN
CORE_CONTRACT_DELEGATION_SHARD = CORE_CONTRACT_SHARD_BEGIN + 1
CORE_CONTRACT_REGULATION_GLOBAL = CORE_CONTRACT_COIN_GLOBAL + 2
CORE_CONTRACT_COIN = CORE_CONTRACT_ADDRESS_BEGIN
CORE_CONTRACT_DELEGATION = CORE_CONTRACT_COIN + 6
CORE_CONTRACT_REGULATION = CORE_CONTRACT_COIN + 8

CORE_CONTRACT_RVM = 0x3F

CONTRACT_INVALID = 0
DAPP_ID_CORE = 1

#					  [Low -------------------------------------------------- 64b ------------------------------------------------------------ High]
# ContractId:         [----------------- 20b ----------------][     SerialNum:12b    ][ 4b ][                      DAppId:28b                      ]
# ContractVersionId:  [   Build:8b   ][--------- 12b --------][     SerialNum:12b    ][ 4b ][                      DAppId:28b                      ]
# ContractScopeId:    [----- 8b -----][       Scope:12b      ][     SerialNum:12b    ][ 4b ][                      DAppId:28b                      ]

class ContractID(int):
    sn = None
    engine_id = None
    dapp_id = None
    def __new__(cls,value = 0, sn = None, engine_id = None, dapp_id = None):
        if sn is None and engine_id is None and dapp_id is None:
            val = int(value)
            sn = (val >> 20) & 0xFFF
            engine_id = (val >> (20 + 12)) & 0xF
            dapp_id = (val >> (20 + 12 + 4)) & 0xFFFFFFF
            value = val
        else:
            value = ((dapp_id & 0xFFFFFFF) << (20 + 12 + 4)) | ((engine_id & 0xF) << (20 + 12)) | ((sn & 0xFFF) << 20)
        obj = int.__new__(cls, value)
        obj.sn = sn
        obj.dapp_id = dapp_id
        obj.engine_id = engine_id
        return obj
    
    def __repr__(self):
        return f"ContractID(value=0x{int(self):X}, sn={self.sn}, engine_id={self.engine_id}, dapp_id={self.dapp_id})"
    
    def is_core_dapp(self):
        return self.dapp_id == DAPP_ID_CORE and self.engine_id == EngineID.Core.value
    
    def get_scope(self):
        return int(self) & 0xFFF00

    def get_build(self):
        return int(self) & 0xFF
    
class ContractVersionID(ContractID):
    build = None
    def __new__(cls,value = 0, sn = None,engine_id = None, dapp_id = None,build = None):
        if sn is None and engine_id is None and dapp_id is None and build is None:
            val = int(value)
            build = val & 0xFF 
            sn = (val >> 20) & 0xFFF
            engine_id = (val >> (20 + 12)) & 0xF
            dapp_id = (val >> (20 + 12 + 4)) & 0xFFFFFFF
            value = val
        else:
           value = ((dapp_id & 0xFFFFFFF) << (20 + 12 + 4)) | ((engine_id & 0xF) << (20 + 12)) | ((sn & 0xFFF) << 20) |  (build & 0xFF)
        obj = int.__new__(cls, value)
        obj.sn = sn
        obj.engine_id = engine_id
        obj.dapp_id = dapp_id
        obj.build = build
        return obj
    def __repr__(self):
        return f"ContractID(value=0x{int(self):X}, sn={self.sn}, engine_id={self.engine_id}, dapp_id={self.dapp_id}, build={self.build})"

class ContractScopeID(ContractID):
    scope = None
    def __new__(cls,value = 0,sn = None,engine_id = None, dapp_id = None,scope = None):
        if sn is None and engine_id is None and dapp_id is None:
            val = int(value)
            scope = (val>>8) & 0xFFF 
            sn = (val >> 20) & 0xFFF
            engine_id = (val >> (20 + 12)) & 0xF
            dapp_id = (val >> (20 + 12 + 4)) & 0xFFFFFFF
            value = val
        else:
           value = ((dapp_id & 0xFFFFFFF) << (20 + 12 + 4)) | ((engine_id & 0xF) << (20 + 12)) | ((sn & 0xFFF) << 20) |  ((scope & 0xFFF) << 8)
        obj = int.__new__(cls, value)
        obj.sn = sn
        obj.engine_id = engine_id
        obj.dapp_id = dapp_id
        obj.scope = scope
        return obj
    def __repr__(self):
        return f"ContractID(value=0x{int(self):X}, sn={self.sn}, engine_id={self.engine_id}, dapp_id={self.dapp_id}, scope={self.scope})"

class ContractInvokeID(ContractID):
    build = None
    scope = None
    def __new__(cls,value = 0,sn = None,engine_id = None, dapp_id = None,scope = None,build = None):
        if sn is None and engine_id is None and dapp_id is None:
            val = int(value)
            build = val & 0xFF 
            scope = (val>>8) & 0xFFF 
            sn = (val >> 20) & 0xFFF
            engine_id = (val >> (20 + 12)) & 0xF
            dapp_id = (val >> (20 + 12 + 4)) & 0xFFFFFFF
            value = val
        else:
           value = ((dapp_id & 0xFFFFFFF) << (20 + 12 + 4)) | ((engine_id & 0xF) << (20 + 12)) | ((sn & 0xFFF) << 20) |  ((scope & 0xFFF) << 8) | (build & 0xFF)
        obj = int.__new__(cls, value)
        obj.sn = sn
        obj.engine_id = engine_id
        obj.dapp_id = dapp_id
        obj.build = build
        obj.scope = scope
        return obj
    def __repr__(self):
        return f"ContractID(value=0x{int(self):X}, sn={self.sn}, engine_id={self.engine_id}, dapp_id={self.dapp_id}, scope={self.scope},build={self.build})"
        

def CoreContractIDFromRvm(cid:ContractID):
    assert cid.is_core_dapp()
    ret = cid.sn
    if ret == CORE_CONTRACT_COIN and cid.get_scope() == Scope.Global.value:
        ret = CORE_CONTRACT_COIN_GLOBAL
    elif ret == CORE_CONTRACT_DELEGATION and cid.get_scope() == Scope.Shard.value:
        ret = CORE_CONTRACT_DELEGATION_SHARD
    elif ret == CORE_CONTRACT_REGULATION and cid.get_scope == Scope.Global.value:
        ret = CORE_CONTRACT_REGULATION_GLOBAL
    return ret

if __name__ == "__main__":
    cid = ContractID(73148661760)
    cvid = ContractVersionID(73148661761)
    print(cid)
    print(cvid)
