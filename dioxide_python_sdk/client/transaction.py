"""
  dioxtransactionpy defined transaction data struct on chain.
  @author: long
  @date: 2024-09-12
"""
import time,math
from .contract import *
from .account import *

DEFAULT_TRANSCTION_VERSION = 108
DEFAULT_TRANSCTION_TTL = 120 #2 hours
TXN_GAS_PRICE_DEFAULT = 100
TXN_GAS_LIMIT_DEFAULT = 500000


class InternalTargetMode(Enum):
	ITM_NONE = 0
	ITM_SCOPE_ADDRESS = 1		
	ITM_SCOPE_UINT32 = 2		
	ITM_SCOPE_UINT64 = 3		
	ITM_SCOPE_UINT96 = 4		
	ITM_SCOPE_UINT128 = 5	
	ITM_SCOPE_UINT160 = 6	
	ITM_SCOPE_UINT256 = 7	
	ITM_SCOPE_UINT336 = 8	
	ITM_SCOPE_UINT512 = 9	
	ITM_MINER = 10
	ITM_FIRST_SIGNER = 11		
	ITM_SHARD = 12	
	ITM_GLOBAL = 13		
	ITM_GLOBAL_TO_SHARDS = 14
	ITM_END = 15
	ITM_BITMASK = 0xF

class TxnGenerationMode(Enum):
	TGM_USER_SIGNED	= 0
	TGM_PERIODIC_USER = 0x10
	TGM_PERIODIC_SYSTEM	= 0x20
	TGM_RELAY = 0x50					
	TGM_DEFERRED = 0x60
	TGM_GLOBAL_TO_SHARDS = 0x70


class InternalTxnFlag(Enum):
	TMF_NONE = 0
	TMF_GROUPED	= 0x100	
	TMF_EMIITTER_EMBEDDED = 0x200
	TMF_ZERO_ARG = 0x400
	TMF_EXTERNAL = 0x800
	TMF_BITMASK	 = 0xF00

class UnsignedTransaction:
    def __init__(self,contract_invoke_id:ContractInvokeID,opcode,version = DEFAULT_TRANSCTION_VERSION, timestamp = int(time.time_ns()//1_000_000), delegatee:DioxAddress = None):
        self.version = version
        self.packflag = 0
        self.delegatee = delegatee
        self.timestamp = timestamp
        self.mode = TxnGenerationMode.TGM_USER_SIGNED.value
        self.ttl = DEFAULT_TRANSCTION_TTL
        self.sc = 1
        self.tsc = 0
        self.opcode = opcode
        self.isn = 0
        self.fca_token = bytearray()
        self.gas_price = TXN_GAS_PRICE_DEFAULT
        self.gas_limit = TXN_GAS_LIMIT_DEFAULT
        self.rvm_contract = None

        if contract_invoke_id.is_core_dapp():
            self.core_contract = CoreContractIDFromRvm(contract_invoke_id)
            self.build = int(contract_invoke_id.build)
        else:
            self.core_contract = int(CORE_CONTRACT_RVM) + int(contract_invoke_id.get_scope() << CORE_CONTRACT_SCOPE_BITSHIFT)
            self.rvm_contract = contract_invoke_id
        
        if self.core_contract >> CORE_CONTRACT_SCOPE_BITSHIFT == Scope.Address.value:
            if self.delegatee is None:
                self.mode |= InternalTargetMode.ITM_FIRST_SIGNER.value
            else:
                self.mode |= InternalTargetMode.ITM_SCOPE_ADDRESS.value
        else:
            self.mode |= InternalTargetMode.ITM_SHARD.value
        
        self.input_size = 0
        self.input = bytearray()
        
    def set_isn(self,isn):
        self.isn = isn    

    def set_gas_price(self,gas_price):
        self.gas_price = gas_price
    
    def set_gas_limit(self,gas_limit):
         self.gas_limit = gas_limit

    def add_fca(self,token_id:int,amount:int):
        self.fca_token.extend(token_id.to_bytes(8,byteorder='little'))
        amount_len = (amount.bit_length() + 7)//8
        self.fca_token.extend(amount.to_bytes(amount_len,byteorder='little'))
        self.tsc += 1
    

    def set_input(self,args,abi):
        if args is None:
            self.mode |= InternalTxnFlag.TMF_ZERO_ARG.value
        if self.rvm_contract.is_core_dapp():
            pass
        else:
            pass

    def serialize(self)->bytes:
        res = bytearray()
        res.extend(self.version.to_bytes(1,'little'))
        res.extend(self.packflag.to_bytes(1,'little'))
        res.extend(self.timestamp.to_bytes(6,'little'))
        res.extend(self.isn.to_bytes(4,'little'))
        ttl_sc_tsc =  ((self.tsc & 0x3) << 13) | (((self.sc-1) & 0xF) << 9)  | ((self.ttl-1) & 0x1FF)
        res.extend(ttl_sc_tsc.to_bytes(2,'little'))
        res.extend(self.mode.to_bytes(2,'little'))
        res.extend(self.opcode.to_bytes(1,'little'))
        res.extend(self.core_contract.to_bytes(1,'little'))

        gas_price_exp = 0
        gas_price_mantissa = 0
        tmp = 0
        if self.gas_price != 0:
            tmp = int(math.log2(self.gas_price)) + 1
        if tmp > 32:
            gas_price_exp = tmp - 32
            gas_price_mantissa = (self.gas_price >> (tmp-32)) & 0xFFFFFFFF
        else:
             gas_price_exp = 0
             gas_price_mantissa = self.gas_price & 0xFFFFFFFF

        res.extend(gas_price_mantissa.to_bytes(4,'little'))
        res.extend(gas_price_exp.to_bytes(2,'little'))
        res.extend(self.gas_limit.to_bytes(4,'little'))
        if self.rvm_contract is None:
            res.extend(self.build.to_bytes(1,'little'))
        else:
            res.extend(self.rvm_contract.to_bytes(8,'little'))
        
        if self.delegatee is not None:
            res.extend(self.delegatee.address_bytes)

        res.extend(self.input_size.to_bytes(2,'little'))
        res.extend(self.input)
        return bytes(res)

    def hash(self):
        pass

if __name__ == "__main__":
    dapp_address = DioxAddress(None,DioxAddressType.DAPP)
    dapp_address.set_delegatee_from_string("testa")
    tx = UnsignedTransaction(ContractInvokeID(73152856577),0,timestamp=1756808332132,delegatee=dapp_address)
    tx.set_gas_limit(74)
    raw_tx = tx.serialize()
    print(raw_tx.hex().upper())
