from .types import KeyedStateMsgKeyName,AllStateMsgKeyName

#dapp filter,filter state update info which associate with a specific dapp
def dapp_filter(dapp_name):
    def filter(r):
        for scope in AllStateMsgKeyName:
            for state in r.get(f"{scope}",[]):
                if state.get("Contract",None) is not None and state["Contract"].split('.')[0] == dapp_name:
                    return True
        return False
    return filter

def contract_filter(contract_name):
    def filter(r):
        for scope in AllStateMsgKeyName:
            for state in r.get(f"{scope}",[]):
                if state.get("Contract",None) is not None and ".".join(state["Contract"].split(".")[:2]) == contract_name:
                    return True
        return False
    return filter

def scopekey_filter(scopekey:str):
    def filter(r):
        for scope in KeyedStateMsgKeyName:
            for state in r.get(f"{scope}",[]):
                if state.get("Key",None) is not None and state["Key"] == scopekey:
                    return True
        return False
    return filter

def contract_and_scopekey_filter(contract_name,scopekey):
    def filter(r):
        for scope in KeyedStateMsgKeyName:
            for state in r.get(f"{scope}",[]):
                if (state.get("Key",None) is not None and state["Key"] == scopekey) and \
                    (state.get("Contract",None) is not None and ".".join(state["Contract"].split(".")[:2]) == contract_name):
                    return True
        return False
    return filter

def contract_and_statekey_filter(contract_name,statekey:str):
    def filter(r):
        for scope in AllStateMsgKeyName:
            for state in r.get(f"{scope}",[]):
                if (state.get("State",None) is not None and state["State"].get(statekey,None) != None) and \
                    (state.get("Contract",None) is not None and ".".join(state["Contract"].split(".")[:2]) == contract_name):
                    return True
        return False
    return filter

def height_filter(start,end):
    def filter(r):
        return r.get("Height",None) is not None and r["Height"]>=start and r["Height"]<end
    return filter

