"""
  dioxclientpy is a python client for dioxide node.
  @author: long
  @date: 2024-09-12
"""
from ..client import clientlogger
from ..client.stat import StatTool
from ..config.client_config import Config
from ..utils.rpc import HTTPProvide
from ..client.account import DioxAccount,DioxAddress,DioxAddressType
from ..utils.gadget import exception_handler,get_subscribe_message,progress_bar
from ..client.filters import (
    dapp_filter,
    contract_filter,
    scopekey_filter,
    contract_and_scopekey_filter,
    contract_and_statekey_filter,
    height_filter,
    external_relay_filter
)
from ..client.handlers import (
    default_handler,
    default_dapp_state_handler,
    default_contract_state_handler,
    default_scopekey_state_handler,
    default_contract_scopekey_state_handler,
    default_contract_statekey_state_handler
)
from box import Box  # type: ignore
from . import types as dioxtypes
import queue
import base64
import time
import json
from ..client.contract import Scope
import os
import threading
import websockets  # type: ignore
from concurrent.futures import ThreadPoolExecutor
import asyncio


DEFAULT_TIMEOUT = 60

class DioxError(Exception):
    code = None
    message = None
    def __init__(self, c,m):
        self.code = c
        self.message = m
    def info(self):
        return "code :{},message : {}".format(self.code, self.message)

#-----------------------------------------------------------------------------------------------------
class DioxClient:
    rpc = None
    logger = clientlogger.client_logger
    ws_rpc = None
    ws_connections = None

    def __init__(self,url = Config.rpc_url,ws_url = Config.ws_rpc):
        self.rpc = HTTPProvide(url)
        self.rpc.logger = self.logger
        self.ws_rpc = ws_url
        self.ws_connections = {}
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.__start_loop, daemon=True).start()

    def __start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def get_client_version(self):
        info = "url:{}\n".format(Config.url)
        info = "rpc:{}\n".format(self.rpc)
        info = "version:{}\n".format(1.0)
        return info

    def make_request(self,method,params):
        stat = StatTool.begin()
        response = self.rpc.make_request(method, params)
        stat.done()
        e = self.error_response(response)
        if e is not None:
            memo = "ERROR {}:{}".format(response["err"],response["ret"])
            stat.debug("request:{}:{}".format(method,memo))
            raise e
        else:
            stat.debug("request:{}:{}".format(method,"DONE"))
            return response["ret"]

    def error_response(self,response):
        if response is None:
            e = DioxError(-1,"response is None")
            return e
        if("err" in response):
            msg = response["ret"]
            code = response["err"]
            self.logger.error("request error: {}, msg:{} ".format(code,msg) )
            e = DioxError(code,msg)
            return e
        return None

#rpc method ----------------------------------------------------------------
    """
    @description:
        Return chain overview.
    @params:
        None
    @response -- object:
        VersionName: string - chain version/network type
        DeployName: string - deploy name, [VersionName]+'@dioxide'
        ChainVersion: uint8 - chain version
        Time: uint64 - current network time
        BlockTime: uint64 - current chainhead block timestamp
        ShardOrder: uint32 - shard order, shard count = 1+(1<<ShardOrder)
        ShardOnDuty: array - [shard start index, running shard count]
        BlackListSize: uint64 - block blacklist size
        ScalingOut: bool - whether scale-out is in progress
        Rebase: bool - whether rebase is in progress
        BlockFallBehind: uint32 - height lag vs network latest
        BaseHeight: uint64 - chain base height (rebase affects this)
        HeadHash: string - latest master block hash (base32)
        HeadHeight: uint64 - latest height
        FinalizedBlock: array - [last finalized block_hash, block_height]
        ArchivedHeight: array - [last archived block_hash, block_height]
        AvgGasPrice: string - avg gas fee
        TxnCount: array - [ScheduledTxnCount,ConfirmedTxnCount,...]

        When not in rebase, also returns:
        IdAllocated: array - [max allocated block id, max allowed block id]
        Throughput: float - throughput
        BlockInterval: float - block interval (ms)
        HashRate: uint64 - hash rate
        ForkRate: float - fork rate
        FinalityDistance: uint64 - distance from latest to last finalized
        Difficulty: uint64 - pow difficulty
        Global: object - global shard info (throughput, txcount, etc.)
        Shards: array - per-shard info
    """
    @exception_handler
    def get_overview(self):
        return self.make_request("dx.overview",{})


    """
    @description:
        Return current block height.
    @params:
        None
    @response -- int:
        Latest block height synced by this node.
    """
    @exception_handler
    def get_block_number(self):
        respone = self.make_request("dx.committed_head_height",{})
        return int(respone["HeadHeight"])

    """
    @description:
        Return shard_index for the given key.
    @params:
        scope: global/shard/address/uds(user define scope)
        scope_key: key for scope; may be empty if scope is global
    @response -- int:
        Shard index for the key.
    """
    @exception_handler
    def get_shard_index(self,scope,scope_key):
        method = "dx.shard_index"
        params = {}
        params.update({"scope":scope})
        params.update({"scope_key":scope_key})
        response = self.make_request(method,params)
        return int(response["ShardIndex"])

    """
    @description:
        Return ISN for address (like Ethereum nonce).
    @params:
        address: user/dapp/token address
    @response -- int:
        ISN for the address.
    """
    @exception_handler
    def get_isn(self,address):
        method = "dx.isn"
        params = {}
        params.update({"address":address})
        response = self.make_request(method,params)
        return int(response["ISN"])

    """
    @description:
        Get consensus_header by height.
    @params:
        height: block height
    @response -- object:
        Size, Version, Prev, Height, ShardOrder, Timestamp,
        ScheduledTxnCount, UserInitiatedTxnCount, IntraRelayTxnCount, etc.,
        ShardBlockMerkle, ShardChainStateMerkle, ShardProcessedTxnMerkle,
        ShardOutboundRelayMerkle, GlobalChainStateMerkle, GlobalProcessedTxnMerkle,
        Consensus, Miner, TotalGasFee, AvgGasPrice, ScalingNext, SnapshotCarried,
        Uncles, PowDifficulty, PowNonce, Hash, BlockInterval, Throughput,
        ForkRate, Stage, DispatchedRelayTxnCount
    """
    @exception_handler
    def get_consensus_header_by_height(self,height):
        method = "dx.consensus_header"
        params = {}
        params.update({"query_type":0})
        params.update({"height":height})
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get consensus_header by block hash.
    @params:
        hash: block hash
    @response -- object:
        Same as get_consensus_header_by_height.
    """
    @exception_handler
    def get_consensus_header_by_hash(self,hash:str):
        method = "dx.consensus_header"
        params = {}
        params.update({"query_type":1})
        params.update({"hash":hash})
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get transaction block by shard index and height.
    @params:
        shard_index: shard index
        height: block height
    @response -- object:
        Size, Version, Scope, Shard, Prev, ScheduledTxnCount,
        UserInitiatedTxnCount, IntraRelayTxnCount, InboundRelayTxnCount,
        OutboundRelayTxnCount, DeferredRelayTxnCount, DispatchedRelayTxnCount,
        ExecutionCount, ConsensusHeaderHash, ConfirmedTxnMerkle, ChainStateMerkle,
        Hash, Height, Timestamp, Miner, State, Transactions
    """
    @exception_handler
    def get_transaction_block_by_height(self,shard_index,height):
        method = "dx.transaction_block"
        params = {}
        params.update({"query_type":0})
        params.update({"shard_index":shard_index})
        params.update({"height":height})
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get transaction block by shard index and block hash.
    @params:
        shard_index: shard index
        hash: block hash
    @response -- object:
        Same as get_transaction_block_by_height.
    """
    @exception_handler
    def get_transaction_block_by_hash(self,shard_index,hash:str):
        method = "dx.transaction_block"
        params = {}
        params.update({"query_type":1})
        params.update({"shard_index":shard_index})
        params.update({"hash":hash})
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get transaction by hash.
    @params:
        hash: transaction hash
    @response -- object:
        Hash, GasOffered, GasPrice, Grouped, uTxnSize, Mode,
        Function, Input, Invocation, Stage, Height, Shard, ConfirmState
    """
    @exception_handler
    def get_transaction(self,hash:str,shard_index=None):
        method = "dx.transaction"
        params = {}
        tx_hash = hash
        tx_shard = shard_index
        if ":" in hash:
            base, suffix = hash.split(":", 1)
            if suffix.isdigit():
                tx_hash = base
                if tx_shard is None:
                    tx_shard = int(suffix)
        params.update({"hash": tx_hash})
        if tx_shard is not None:
            params.update({"shard_index": tx_shard})
        response = self.make_request(method, params)
        return Box(response, default_box=True)

    """
    @description:
        Compose transaction: pack fields into bytes for signing and sending.
    @params:
        sender: sender address
        function: contract function (<dapp>.<contract>.<function>)
        args: function args, object
        isn: transaction ISN (default latest, like Ethereum nonce)
        is_delegatee: whether delegated tx
        gas_price: gas price
        gas_limit: gas limit
    @response -- bytes
        Composed transaction, base64 decoded.
    """
    @exception_handler
    def compose_transaction(self,sender,function:str,args:dict,tokens:list=None,isn=None,is_delegatee=False,gas_price=None,gas_limit=None,ttl=None):
        method = "tx.compose"
        params = {}
        params.update({"function":function})
        params.update({"args":args})
        if is_delegatee:
            params.update({"delegatee":sender})
        else:
            params.update({"sender":sender})
        if gas_price is not None:
            params.update({"gasprice":gas_price})
        if gas_limit is not None:
            params.update({"gaslimit":gas_limit})
        if isn is not None:
            params.update({"isn":isn})
        if tokens is not None:
            params.update({"tokens":tokens})
        if ttl is not None:
            params.update({"ttl":ttl})
        response = self.make_request(method,params)
        return base64.b64decode(response["TxData"])

    """
    @description:
        Build transaction locally without RPC (inverse of parse logic).
    @params:
        sender: sender address or DioxAccount
        function: contract function (<dapp>.<contract>.<function>)
        args: function args, dict keyed by param name
        signature: function signature e.g. "address:to,uint32:amount"; optional, from contract if not provided
        contract_info: contract info object (optional), from RPC if not provided
        isn: transaction ISN (default latest)
        is_delegatee: whether delegated tx
        gas_price: gas price
        gas_limit: gas limit
        ttl: transaction TTL
    @response -- bytes
        Unsigned transaction bytes.
    """
    @exception_handler
    def compose_transaction_local(self, sender, function: str, args: dict, signature: str = None,
                                  contract_info=None, isn=None, is_delegatee=False,
                                  gas_price=None, gas_limit=None, ttl=None):
        from ..utils.gadget import serialize_args
        from .transaction import UnsignedTransaction
        from .contract import ContractInvokeID, ContractID, ContractVersionID
        from .account import DioxAddress, DioxAddressType

        parts = function.split(".")
        if len(parts) != 3:
            raise DioxError(-10003, f"Invalid function format: {function}, expected 'dapp.contract.function'")

        dapp_name, contract_name, function_name = parts

        if contract_info is None:
            contract_info = self.get_contract_info(dapp_name, contract_name)

        contract_id_val = contract_info.ContractID
        contract_version_id_val = contract_info.ContractVersionID

        contract_id = ContractID(contract_id_val)
        contract_version_id = ContractVersionID(contract_version_id_val)

        function_info = None
        functions = contract_info.Functions if hasattr(contract_info, 'Functions') else []
        for func in functions:
            func_name = func.get("Name") if isinstance(func, dict) else getattr(func, "Name", None)
            if func_name == function_name:
                function_info = func
                break

        if function_info is None:
            raise DioxError(-10004, f"Function {function_name} not found in contract {dapp_name}.{contract_name}")

        if signature is None:
            params = function_info.get("Params", []) if isinstance(function_info, dict) else getattr(function_info, "Params", [])
            if not params:
                signature = ""
            else:
                sig_parts = []
                for param in params:
                    if isinstance(param, dict):
                        param_type = param.get("Type", "")
                        param_name = param.get("Name", "")
                    else:
                        param_type = getattr(param, "Type", "")
                        param_name = getattr(param, "Name", "")
                    sig_parts.append(f"{param_type}:{param_name}")
                signature = ",".join(sig_parts)

        opcode = function_info.get("Opcode", 0) if isinstance(function_info, dict) else getattr(function_info, "Opcode", 0)

        dapp_id = contract_id.dapp_id
        engine_id = contract_id.engine_id
        sn = contract_id.sn
        build = contract_version_id.build

        scope_value = (contract_id.get_scope() >> 8) & 0xFFF

        contract_invoke_id = ContractInvokeID(
            sn=sn,
            engine_id=engine_id,
            dapp_id=dapp_id,
            scope=scope_value,
            build=build
        )

        delegatee = None
        if is_delegatee:
            if isinstance(sender, str):
                delegatee = DioxAddress(None, DioxAddressType.DAPP)
                if not delegatee.set_delegatee_from_string(sender):
                    raise DioxError(-10005, f"Invalid delegatee: {sender}")
            else:
                delegatee = DioxAddress(sender.address_bytes, DioxAddressType.DEFAULT)

        tx = UnsignedTransaction(contract_invoke_id, opcode, delegatee=delegatee)

        if isn is not None:
            tx.set_isn(isn)
        else:
            sender_addr = sender.address if hasattr(sender, 'address') else sender
            tx.set_isn(self.get_isn(sender_addr))

        if gas_price is not None:
            tx.set_gas_price(gas_price)
        if gas_limit is not None:
            tx.set_gas_limit(gas_limit)
        if ttl is not None:
            tx.ttl = ttl

        if args and signature:
            serialized_input = serialize_args(signature, args)
            tx.input = bytes.fromhex(serialized_input)
            tx.input_size = len(tx.input)
        elif not args:
            tx.mode |= 0x400

        return tx.serialize()

    """
    @description:
        Send signed transaction.
    @params:
        signed_txn: signed transaction bytes
        sync: wait for result
        timeout: timeout
    @response -- str
        Transaction hash (base32).
    """
    @exception_handler
    def send_raw_transaction(self,signed_txn:bytes,sync=False,timeout=DEFAULT_TIMEOUT):
        method = "tx.send"
        params = {"txdata":base64.b64encode(signed_txn).decode()}
        response = self.make_request(method,params)
        tx_hash = response["Hash"]
        if sync:
            if self.wait_for_transaction_confirmed(tx_hash,timeout):
                return tx_hash
            else:
                raise DioxError(-10000, "timeout")
        return tx_hash


    """
    @description:
        Get contract details by name (like ABI).
    @params:
        dapp_name: dapp name
        contract_name: contract name
    @response -- object
        ContractID, ContractVersionID, Contract, Hash, ImplmentedInterfaces,
        StateVariables, Scopes, Interfaces, Functions
    """
    @exception_handler
    def get_contract_info(self,dapp_name,contract_name):
        method = "dx.contract_info"
        params = {"contract":"{}.{}".format(dapp_name,contract_name)}
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get source code of deployed contract.
    @params:
        dapp_name: dapp name
        contract_name: contract name
    @response -- str
        Contract source code string.
    """
    @exception_handler
    def get_source_code(self,dapp_name,contract_name):
        method = "dx.source_code"
        params = {"contract":"{}.{}".format(dapp_name,contract_name)}
        response = self.make_request(method,params)
        return response

    """
    @description:
        Deploy contract.
    @params:
        dapp_name: dapp name
        delegator: dapp owner, signing account
        file_path: path to .prd file
        source_code: required if file_path not set
        construct_args: constructor args, object
        compile_time: max compile time (optional)
    @response -- str
        Deploy transaction hash.
    """
    @exception_handler
    def deploy_contract(self,dapp_name,delegator:DioxAccount,file_path=None,source_code=None,construct_args:dict=None,compile_time=None):
        deploy_args={}
        if file_path is not None:
            with open(file_path) as f:
                deploy_args.update({"code":[f.read()]})
        else:
            if source_code is None or (isinstance(source_code, str) and source_code.strip() == ""):
                raise DioxError(-10001, "params error")
            deploy_args.update({"code":[source_code]})
        if construct_args is None:
            deploy_args.update({"cargs": [""]})
        else:
            deploy_args.update({"cargs": [json.dumps(construct_args)]})
        if compile_time is not None:
            deploy_args.update({"time":compile_time})
        dapp_address = DioxAddress(None,DioxAddressType.DAPP)
        if not dapp_address.set_delegatee_from_string(dapp_name):
            raise DioxError(-10002, "invalid dapp name")
        deployed_txn = self.compose_transaction(
            sender=dapp_address.address,
            function="core.delegation.deploy_contracts",
            args=deploy_args,
            is_delegatee=True
        )
        tx_hash = self.send_raw_transaction(delegator.sign_diox_transaction(deployed_txn),True)
        self.wait_for_deploy(tx_hash)
        return tx_hash

    """
    @description:
        Deploy multiple contracts.
    @params:
        dapp_name: dapp name
        delegator: dapp owner, signing account
        contracts: dict mapping absolute path -> constructor args
        compile_time: max compile time (optional)
    @response -- str
        Deploy transaction hash.
    """
    @exception_handler
    def deploy_contracts(self,dapp_name,delegator:DioxAccount,contracts:dict[str,dict]=None,compile_time=None):
        deploy_args={}
        codes = []
        cargs = []

        if contracts is None or len(contracts) == 0:
            raise DioxError(-10004, "contracts parameter is required and cannot be empty")

        # Process contracts in dictionary order (Python 3.7+ maintains insertion order)
        # This ensures codes and cargs maintain the same correspondence
        for contract_path in contracts.keys():
            # Normalize path to handle different path formats
            normalized_path = os.path.normpath(contract_path)
            with open(normalized_path) as f:
                codes.append(f.read())

            # Get constructor args for this contract
            carg = contracts[contract_path]
            if carg is None:
                cargs.append("")
            else:
                cargs.append(json.dumps(carg))
        deploy_args.update({"code":codes})
        deploy_args.update({"cargs":cargs})
        if compile_time is not None:
            deploy_args.update({"time":compile_time})
        dapp_address = DioxAddress(None,DioxAddressType.DAPP)
        if not dapp_address.set_delegatee_from_string(dapp_name):
            raise DioxError(-10002, "invalid dapp name")
        deployed_txn = self.compose_transaction(
            sender=dapp_address.address,
            function="core.delegation.deploy_contracts",
            args=deploy_args,
            is_delegatee=True
        )
        tx_hash = self.send_raw_transaction(delegator.sign_diox_transaction(deployed_txn),True)
        self.wait_for_deploy(tx_hash)
        return tx_hash

    @exception_handler
    def wait_for_deploy(self,deploy_hash):
        state = self.get_contract_state("core","contracts",Scope.Global,None).State
        target_height = -1
        if state is not None and state != {}:
            for s in state.Scheduled:
                if s.BuildKey == deploy_hash:
                    target_height = s.TargetHeight
                    break
        base = cur_height = self.get_block_number()
        while cur_height <= target_height:
            progress_bar(cur_height-base,target_height-base,title="Deploy Process: ")
            cur_height = self.get_block_number()
            time.sleep(0.5)
        print("\nDeploy finish.")

    """
    @description:
        Get contract state.
    @params:
        contract_with_scope: state scope (global | shard | address | uint32 | ...)
        scope_key: key for scope (e.g. address when scope is address; empty for global)
    @response -- object
        State object.
    """
    @exception_handler
    def get_contract_state(self,dapp_name,contract_name,scope:Scope,key):
        method = "dx.contract_state"
        params = {"contract_with_scope":str(dapp_name)+"."+str(contract_name)+"."+scope.name.lower()}
        if scope.value != scope.Global.value:
            params.update({"scope_key":key})
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get dapp info.
    @params:
        dapp_name: dapp name
    @response -- object
        DappID
    """
    @exception_handler
    def get_dapp_info(self,dapp_name):
        method = "dx.dapp"
        params = {"name":"{}".format(dapp_name)}
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        Get token info.
    @params:
        token_symbol: token symbol (uppercase)
    @response -- object
        TokenId
    """
    @exception_handler
    def get_token_info(self,token_symbol):
        method = "dx.token"
        params = {"symbol":"{}".format(token_symbol)}
        response = self.make_request(method,params)
        return Box(response,default_box=True)


    """
    @description:
        Get events (relay@external) for a transaction.
    @params:
        txhash: transaction hash
    @response -- object
        tx: relay@external transaction (input field needs deserialization by caller)
    """
    @exception_handler
    def get_events_by_transaction(self,txhash):
        tx = self.get_transaction(txhash)
        ret = []
        relays = self.get_all_relay_transactions(tx,detail=True)
        for relay in relays:
            print(relay)
            if relay.get("Mode","").find("TMF_EXTERNAL") != -1:
                ret.append(relay)
        return ret

    #if overflow tcp buffer, consider use message queue
    @exception_handler
    def subscribe(self,topic:dioxtypes.SubscribeTopic,handler=default_handler,filter=None):
        thread_id = threading.get_ident()
        asyncio.set_event_loop(self.loop)
        asyncio.run_coroutine_threadsafe(self.__subscribe(topic,thread_id, handler, filter),self.loop)


    @exception_handler
    def subscribe_state_with_dapp(self,dapp_name,handler=default_handler):
        self.subscribe(dioxtypes.SubscribeTopic.STATE,default_dapp_state_handler(dapp_name,handler),dapp_filter(dapp_name))

    @exception_handler
    def subscribe_state_with_contract(self,dapp_contract_name,handler=default_handler):
        self.subscribe(dioxtypes.SubscribeTopic.STATE,default_contract_state_handler(dapp_contract_name,handler),contract_filter(dapp_contract_name))

    @exception_handler
    def subscribe_state_with_scpoekey(self,scopekey:str,handler=default_handler):
        self.subscribe(dioxtypes.SubscribeTopic.STATE,default_scopekey_state_handler(scopekey,handler),scopekey_filter(scopekey))

    @exception_handler
    def subscribe_state_with_contract_and_scopekey(self,dapp_contract_name,scopekey:str,handler=default_handler):
        self.subscribe(dioxtypes.SubscribeTopic.STATE,default_contract_scopekey_state_handler(dapp_contract_name,scopekey,handler),contract_and_scopekey_filter(dapp_contract_name,scopekey))

    @exception_handler
    def subscribe_state_with_contract_and_statekey(self,dapp_contract_name,statekey:str,handler=default_handler):
        self.subscribe(dioxtypes.SubscribeTopic.STATE,default_contract_statekey_state_handler(dapp_contract_name,statekey,handler),contract_and_statekey_filter(dapp_contract_name,statekey))

    @exception_handler
    def subscribe_external_relay(self, name = None,handler = default_handler):
        self.subscribe(dioxtypes.SubscribeTopic.RELAYS,handler,external_relay_filter(name))

    @exception_handler
    def subscribe_block_with_height(self,topic:dioxtypes.SubscribeTopic,start=0,end=0xffffffff,handler=default_handler):
        self.subscribe(topic,handler,height_filter(start,end))

    @exception_handler
    def unsubscribe(self,thread_id):
        ws = self.ws_connections.get(thread_id)
        if ws is not None:
            asyncio.run_coroutine_threadsafe(self.__unsubscribe(ws, thread_id),self.loop)

    async def __subscribe(self,topic:dioxtypes.SubscribeTopic,thread_id,handler,filter=None):
        executor = ThreadPoolExecutor(max_workers=Config.default_thread_nums)
        ws = await websockets.connect(self.ws_rpc, ping_interval=None)
        self.ws_connections[thread_id] = ws
        msg = get_subscribe_message(topic)
        await ws.send(msg)
        while ws in self.ws_connections.values():
            resp = json.loads(await ws.recv())
            if (handler is not None) and (filter is None or filter(resp)):
                executor.submit(handler,resp)

    async def __unsubscribe(self, ws, thread_id):
        await ws.close()
        self.ws_connections.pop(thread_id, None)


    #wrapper method ----------------------------------------------------------------
    @exception_handler
    def send_transaction(self,user:DioxAccount,function:str,args:dict,tokens:list=None,isn=None,is_delegatee=False,gas_price=None,gas_limit=None,is_sync=False,timeout=DEFAULT_TIMEOUT):
        sender_addr = user.address
        if ":" not in sender_addr:
            sender_addr = sender_addr + ":" + user.account_type.name.lower()
        unsigned_txn = self.compose_transaction(sender=sender_addr,
                                          function=function,
                                          args=args,
                                          tokens=tokens,
                                          isn=isn,
                                          is_delegatee=is_delegatee,
                                          gas_price=gas_price,
                                          gas_limit=gas_limit
                                        )
        signed_txn = user.sign_diox_transaction(unsigned_txn)
        tx_hash = self.send_raw_transaction(signed_txn,is_sync,timeout)
        return tx_hash

    @exception_handler
    def mint_dio(self,user:DioxAccount,amount,sync=True,timeout=DEFAULT_TIMEOUT):
        tx_hash = self.send_transaction(user=user,function="core.coin.mint",args={"Amount":"{}".format(amount)},is_sync=sync,timeout=timeout)
        return tx_hash

    @exception_handler
    def transfer(self,sender:DioxAccount,receiver,amount,token="DIO",sync=True,timeout=DEFAULT_TIMEOUT):
        args = {
            "To":"{}".format(receiver),
            "Amount":"{}".format(amount),
            "TokenId":"{}".format(token)
        }
        tx_hash = self.send_transaction(user=sender,function="core.wallet.transfer",args=args,is_sync=sync,timeout=timeout)
        return tx_hash

    @exception_handler
    def create_dapp(self,user:DioxAccount,dapp_name,deposit_amount,sync=True,timeout=DEFAULT_TIMEOUT):
        tx_hash = self.send_transaction(
            user=user,
            function="core.delegation.create",
            args={
                "Type":10,
                "Name":"{}".format(dapp_name),
                "Deposit":"{}".format(deposit_amount)
            },
            is_sync=sync
        )
        if sync:
            ok = self.wait_for_dapp_deployed(tx_hash,timeout)
        else:
            ok = None
        return tx_hash,ok

    """
    @description:
        Create token.
    @params:
        Minter: minter contract CID; 0 if none or set later
        MinterFlags: 0=disallow(temporary), 1=allow(temporary), 2=disallow(permanent), 3=allow(permanent)
        TokenFlags: 0=can set minter later, 1=cannot
        Symbol: token symbol, uppercase, 3-8 chars
        InitSupply: initial supply
        Deposit: initial DIO deposit for this token
    @response -- object
        State object.
    @TBD: use enum for flags
    """
    @exception_handler
    def create_token(self,user:DioxAccount,symbol,initial_supply,deposit,decimals,cid=0,minter_flag=1,token_flag=0,sync=True,timeout=DEFAULT_TIMEOUT):
        tx_hash = self.send_transaction(
            user=user,
            function="core.delegation.create_token",
            args={
                "Minter":cid,
                "MinterFlags":minter_flag,
                "TokenStates":token_flag,
                "Symbol":"{}".format(symbol),
                "InitSupply":"{}".format(initial_supply),
                "Deposit":"{}".format(deposit),
                "Decimals":decimals
            },
            is_sync=sync
        )
        if sync:
            ok = self.wait_for_token_deployed(tx_hash,timeout)
        else:
            ok = None
        return tx_hash,ok



    #aux method ----------------------------------------------------------------
    def is_tx_confirmed(self,tx):
        if tx is None or tx.get("ConfirmState",None) is None :
            return False
        return tx.ConfirmState in dioxtypes.TXN_CONFIRMED_STATUS

    def is_tx_success(self,tx):
        if tx is None or \
            tx.get("Invocation",None) is None or \
                tx["Invocation"].get("Status",None) is None or \
                tx["Invocation"]["Status"] != "IVKRET_SUCCESS":
            return False
        return True

    def is_tx_confirmed_with_relays(self,tx):
        q = queue.Queue()
        q.put(tx.Hash)
        while not q.empty():
            cur_tx = self.get_transaction(q.get())
            if not self.is_tx_confirmed(cur_tx):
                return False
            for relay_tx_hash in cur_tx.Invocation.get("Relays",[]):
                q.put(relay_tx_hash)
        return True

    def is_tx_success_with_relays(self,tx):
        q = queue.Queue()
        q.put(tx.Hash)
        while not q.empty():
            cur_tx = self.get_transaction(q.get())
            if not self.is_tx_success(cur_tx):
                return False
            for relay_tx_hash in cur_tx.Invocation.get("Relays",[]):
                q.put(relay_tx_hash)
        return True

    def get_all_relay_transactions(self,tx,detail=False):
        res = []
        if self.is_tx_confirmed_with_relays(tx):
            q = queue.Queue()
            q.put(tx)
            while not q.empty():
                for h in q.get().Invocation.get("Relays",[]):
                    res.append(self.get_transaction(h) if detail is True else h)
                    q.put(self.get_transaction(h))
            return res
        else:
            return None

    def wait_for_transaction_confirmed(self,tx_hash,timeout):
        start = time.time()
        tx = self.get_transaction(tx_hash)
        while not self.is_tx_confirmed_with_relays(tx):
            if time.time() - start > timeout:
                return False
            time.sleep(1)
        return True

    def wait_for_dapp_deployed(self,tx_hash,timeout):
        if not self.wait_for_transaction_confirmed(tx_hash,timeout):
            return False
        tx = self.get_transaction(tx_hash)
        if not self.is_tx_success_with_relays(tx):
            return False
        relays = self.get_all_relay_transactions(tx,detail=True)
        for relay in relays:
            if relay.Function == 'core.coin.address.deposit':
                return False
        return True

    def wait_for_token_deployed(self,tx_hash,timeout):
        if not self.wait_for_transaction_confirmed(tx_hash,timeout):
            return False
        tx = self.get_transaction(tx_hash)
        if not self.is_tx_success_with_relays(tx):
            return False
        relays = self.get_all_relay_transactions(tx,detail=True)
        for relay in relays:
            if relay.Function == 'core.coin.address.deposit':
                return False
        return True

    """
    @description:
        Decode transaction input data
    @params:
        tx: Transaction object from get_transaction
    @response -- dict
        Decoded arguments dictionary
    """
    @exception_handler
    def decode_transaction_input(self, tx):
        from ..utils.gadget import deserialized_args

        if not hasattr(tx, 'Function') or not hasattr(tx, 'Input'):
            raise DioxError(-10006, "Transaction object must have Function and Input fields")

        raw = dict(tx) if isinstance(tx, Box) else (tx if isinstance(tx, dict) else None)
        if raw is not None:
            function = raw.get("Function", "") or ""
            input_data = raw.get("Input")
        else:
            function = tx.Function
            input_data = tx.Input
        if isinstance(function, Box):
            function = str(function) if not isinstance(function, str) else function
        if isinstance(input_data, Box):
            input_data = dict(input_data) if input_data else None

        if not function or (isinstance(function, str) and function.strip() == ""):
            return {}

        # If input is already a dictionary (decoded), return it directly
        if isinstance(input_data, dict):
            return input_data

        # If input is empty, return empty dict
        if not input_data or input_data == "":
            return {}

        # Check if this is a core contract function (format: core.module.scope.function)
        parts = function.split(".")
        if len(parts) >= 2 and parts[0] == "core":
            # For core contracts, if input is already decoded (dict), return it
            # Otherwise, we cannot decode core contract inputs without their ABI
            # Return empty dict or the input as-is if it's a string
            if isinstance(input_data, str):
                # Try to parse as hex string and decode if possible
                # For now, return empty dict for core contracts with hex input
                # as we don't have access to core contract ABIs
                return {}
            return input_data

        # For regular contracts, expect format: dapp.contract.function
        if len(parts) != 3:
            raise DioxError(-10003, f"Invalid function format: {function}, expected 'dapp.contract.function'")

        dapp_name, contract_name, function_name = parts

        # Get contract info to find function signature
        try:
            contract_info = self.get_contract_info(dapp_name, contract_name)
        except Exception as e:
            # If contract info cannot be retrieved, return empty dict
            self.logger.warning(f"Cannot get contract info for {dapp_name}.{contract_name}: {e}")
            return {}

        functions = contract_info.Functions if hasattr(contract_info, 'Functions') else []

        function_info = None
        for func in functions:
            func_name = func.get("Name") if isinstance(func, dict) else getattr(func, "Name", None)
            if func_name == function_name:
                function_info = func
                break

        if function_info is None:
            raise DioxError(-10004, f"Function {function_name} not found in contract {dapp_name}.{contract_name}")

        params = function_info.get("Params", []) if isinstance(function_info, dict) else getattr(function_info, "Params", [])
        if not params:
            return {}

        sig_parts = []
        for param in params:
            if isinstance(param, dict):
                param_type = param.get("Type", "")
                param_name = param.get("Name", "")
            else:
                param_type = getattr(param, "Type", "")
                param_name = getattr(param, "Name", "")
            sig_parts.append(f"{param_type}:{param_name}")

        signature = ",".join(sig_parts)

        # input_data should be a hex string at this point
        if not isinstance(input_data, str):
            return {}

        return deserialized_args(signature, input_data)

