from enum import Enum

Scope = Enum('Scope',['Global','Shard','Address'])


CONTRACT_SCOPE_BITS = 12
CONTRACT_SCOPE_SHIFT = 8

CONTRACT_INVALID = 0
DAPP_ID_CORE = 1



def contract_set_scope(x,scope):
    return (x&(~((1<<CONTRACT_SCOPE_BITS)-1)<<CONTRACT_SCOPE_BITS)) | (scope << CONTRACT_SCOPE_SHIFT)

def get_contract_dapp(x):
    return x >> 36
