from .types import KeyedStateMsgKeyName,AllStateMsgKeyName
from copy import deepcopy

def default_handler(r):
    print(r)

def default_dapp_state_handler(dapp_name,to_handler=default_handler):
    def handler(r):
        filtered_msg = deepcopy(r)
        for scope in AllStateMsgKeyName:
            if r.get(f"{scope}",None) is not None:
                filtered_msg[f"{scope}"] = []
            for state in r.get(f"{scope}",[]):
                if state.get("Contract",None) is not None and state["Contract"].split('.')[0] == dapp_name:
                    filtered_msg[f"{scope}"].append(state)
        to_handler(filtered_msg)
    return handler

def default_contract_state_handler(contract_name,to_handler=default_handler):
    def handler(r):
        filtered_msg = deepcopy(r)
        for scope in AllStateMsgKeyName:
            if r.get(f"{scope}",None) is not None:
                filtered_msg[f"{scope}"] = []
            for state in r.get(f"{scope}",[]):
                if state.get("Contract",None) is not None and ".".join(state["Contract"].split(".")[:2]) == contract_name:
                    filtered_msg[f"{scope}"].append(state)
        to_handler(filtered_msg)
    return handler

def default_scopekey_state_handler(scopekey,to_handler=default_handler):
    def handler(r):
        filtered_msg = deepcopy(r)
        for scope in AllStateMsgKeyName:
            if r.get(f"{scope}",None) is not None:
                filtered_msg[f"{scope}"] = []
        for scope in KeyedStateMsgKeyName:
            for state in r.get(f"{scope}",[]):
                if state.get("Key",None) is not None and state["Key"] == scopekey:
                    filtered_msg[f"{scope}"].append(state)
        to_handler(filtered_msg)
    return handler


def default_contract_scopekey_state_handler(contract_name,scopekey,to_handler=default_handler):
    def handler(r):
        filtered_msg = deepcopy(r)
        for scope in AllStateMsgKeyName:
            if r.get(f"{scope}",None) is not None:
                filtered_msg[f"{scope}"] = []
        for scope in KeyedStateMsgKeyName:
            if r.get(f"{scope}",None) is not None:
                filtered_msg[f"{scope}"] = []
            for state in r.get(f"{scope}",[]):
                if (state.get("Key",None) is not None and state["Key"] == scopekey) and \
                    (state.get("Contract",None) is not None and ".".join(state["Contract"].split(".")[:2]) == contract_name):
                    filtered_msg[f"{scope}"].append(state)
        to_handler(filtered_msg)
    return handler

def default_contract_statekey_state_handler(contract_name,statekey,to_handler=default_handler):
    def handler(r):
        filtered_msg = deepcopy(r)
        for scope in AllStateMsgKeyName:
            if r.get(f"{scope}",None) is not None:
                filtered_msg[f"{scope}"] = []
            for state in r.get(f"{scope}",[]):
                if state.get("State",None) is not None and \
                    isinstance(state["State"],dict) and \
                    state["State"].get(statekey,None) != None and \
                    state.get("Contract",None) is not None and \
                    ".".join(state["Contract"].split(".")[:2]) == contract_name:
                    filtered_msg[f"{scope}"].append(state)
        to_handler(filtered_msg)
    return handler

