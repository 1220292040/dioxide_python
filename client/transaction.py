"""
  dioxtransactionpy defined transaction data struct on chain.
  @author: long
  @date: 2024-09-12
"""
import time
import struct
from client import contract


class UnsignedTransaction:
    chain_version = None
    pack_flag = 0
    timestamp = time.time() #HI
    issue_seria_num = None
    ttl_sc_tsc = None
    
    flag_mode = None
    op = None
    contract_id = None
    gas_price = None
    gas_limit = None

    input_size = None
    build_num = None
    rvm_contract_id = None
    target = None
    input = None

    tokens = None
    

    def __init__(self):
        pass
    
    
    def serialize(self):
        format = "!BBHIIHHBBIHIHBQB"
        pass
    
    @staticmethod
    def compose(cvid,opcode,isn,input:bytes,tokens:list=None,gas_price=100,gas_limit=500000,time_to_live=2,signer_count=1,chain_version=64,is_delegatee=False,delegatee=None)->bytes:
        tx = UnsignedTransaction()
        # base transaction info
        tx.chain_version = chain_version
        tx.pack_flag = 0
        tx.timestamp = time.time()
        tx.issue_seria_num = isn
        tx.ttl_sc_tsc = ((time_to_live-1)&0x1f) | (((signer_count-1) & 0x2f) << 5) | ((len(tokens)&0x1f)<<11)

        # invoke info
        # scope of ciid must be address
        tx.flag_mode = (11 if is_delegatee is False else 1) | (0x400 if input is None else 0)
        if contract.get_contract_dapp(cvid) != contract.DAPP_ID_CORE:
            tx.contract_id = (contract.Scope.Address.value<<6) + 0x3f
            tx.rvm_contract_id = contract.contract_set_scope(cvid,contract.Scope.Address.value)
        else:
            tx.contract_id = (cvid >> 20) & 4095
            tx.build_num =  cvid & 255
            
        tx.contract_id = (cvid,contract.Scope.Address.value << 6) + 0x3f
        tx.op = opcode
        tx.gas_price = gas_price
        tx.gas_limit = gas_limit

        tx.input_size = len(input)
        tx.input = input

        if is_delegatee is True:
            tx.target = delegatee

        #TODO serialize tokens

        pass
    

class Transaction:

    def __init__(self):
        pass