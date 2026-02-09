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
        返回区块链整体信息
    @params:
        None
    @response -- object:
        VersionName: string - 区块链版本号名称/网络类型
        DeployName: string - 区块链部署网络的名称,[区块链版本号名称]+'@dioxide'
        ChainVersion: uint8 -  区块链版本号
        Time: uint64 - 当前网络时间
        BlockTime: uint64 - 当前chainhead的区块时间戳
        ShardOrder: uint32 - 分片数量阶,分片数量 = 1+(1<<ShardOrder)
        ShardOnDuty: array - [分片起始序号,正常运行的分片数量]
        BlackListSize: uint64 - 区块黑名单的数量(不接收该哈希值对应的区块)
        ScalingOut: bool - 是否正在执行scale-out(分片扩展)
        Rebase: bool - 是否正在执行rebase操作
        BlockFallBehind: uint32 - 当前节点高度与从区块链网络中接收到最新区块的高度差值
        BaseHeight: uint64 - 区块链的基准高度(rebase操作会影响基准高度值)
        HeadHash: string - 主链上最新区块的master block hash(base32编码)
        HeadHeight: uint64 - 主链最新高度
        FinalizedBlock:array - [最近被finalize的block_hash,最近被finalize的block_height]
        ArchivedHeight: array - [最近被archive的block_hash,最近被archive的block_height]
        AvgGasPrice: string - 区块交易平均gas fee
        TxnCount: array - [ScheduledTxnCount,ConfirmedTxnCount,IntraRelayTxnCount,InboundRelayTxnCount,OutboundRelayTxnCount,DeferredTxnCount]

        如果不是在节点rebase期间,还会返回如下参数：
        IdAllocated: array - [目前已分配的最大block id,允许分配的最大block id],block id是区块在内存中的序号
        Throughput: float - 吞吐量
        BlockInterval: float -  出块间隔(ms)
        HashRate: uint64 - 哈希速率
        ForkRate: float - 分叉率
        FinalityDistance: uint64 - 最后一个finalize的区块高度距离当前最新高度的差值
        Difficulty: uint64: pow难度
        Global: object - global shard的信息,包括throughput,txcount等
        Shards: array - per shard 信息
    """
    @exception_handler
    def get_overview(self):
        return self.make_request("dx.overview",{})


    """
    @description:
        返回当前区块高度
    @params:
        None
    @response -- int:
        返回当前节点所同步到的最新区块高度
    """
    @exception_handler
    def get_block_number(self):
        respone = self.make_request("dx.committed_head_height",{})
        return int(respone["HeadHeight"])

    """
    @description:
        返回指定key所在的shard_index
    @params:
        scope: global/shard/address/uds(user define scope)
        scope_key:对应scope的key,如果scope是global,该字段可以为空
    @response -- int:
        返回对应key所在的shard序号
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
        返回地址对应的isn(类似以太坊的nonce)
    @params:
        address: 地址,可以是用户地址也可以是dapp和token的地址
    @response -- int:
        返回地址对应的isn序号
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
        根据高度获取consensus_header
    @params:
        height: 高度
    @response -- object:
        Size: 区块大小(Byte),
        Version: 链版本,
        Prev: 父区块哈希,
        Height: 高度,
        ShardOrder: 分片数量的阶(分片数量 = 2^ShardOrder),
        Timestamp: 时间戳,
        ScheduledTxnCount: schedule txn的数量,
        UserInitiatedTxnCount: 用户发起的交易数量,
        IntraRelayTxnCount: intra relay txn的数量,
        InboundRelayTxnCount: inbound relay txn数量,
        OutboundRelayTxnCount: outbound relay txn数量,
        DeferredRelayTxnCount: deferred relay txn数量,
        ShardBlockMerkle: 所有shard的txnblock hash组成的merkle tree root,
        ShardChainStateMerkle: 所有shard的txnblock中的ChainStateMerkle组成的merkle tree root,
        ShardProcessedTxnMerkle: 所有shard的txnblock中的transaction merkle tree root组成的merkle tree root,
        ShardOutboundRelayMerkle: 所有shard的txnblock中的outbound relay transaction merkle tree root组成的merkle tree root,
        GlobalChainStateMerkle: global shard的状态变更树树根,
        GlobalProcessedTxnMerkle: global shard的交易树树根,
        Consensus: 共识类型,
        Miner: 矿工地址,
        TotalGasFee: 总gasfee消耗,
        AvgGasPrice: 平均gasprice,
        ScalingNext: 是否进行分片扩展,
        SnapshotCarried: 是否携带snapshot,
        Uncles: 叔块哈希,
        PowDifficulty: 难度,
        PowNonce: nonce值,
        Hash: 区块哈希,
        BlockInterval:出块间隔,
        Throughput: tps,
        ForkRate: 分叉率,
        Stage: 区块状态,
        DispatchedRelayTxnCount: dispatch relay的数量
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
        根据区块哈希获取consensus_header
    @params:
        hash: 哈希
    @response -- object:
        同上
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
        根据分片序号和区块高度获取transaction block
    @params:
        shard_index:分片序号
        height: 高度
    @response -- object:
        Size: 区块大小,
        Version: 区块链版本,
        Scope: 作用域,区分global和normal shard,
        Shard: [当前shard_index, shard_order]
        Prev: 父区块哈希,
        ScheduledTxnCount: schedule txn数量,
        UserInitiatedTxnCount: 用户发起的交易数量,
        IntraRelayTxnCount: intra relay交易数量,
        InboundRelayTxnCount: inbound relay交易数量,
        OutboundRelayTxnCount: outbound relay交易数量,
        DeferredRelayTxnCount: deffered relay交易数量,
        DispatchedRelayTxnCount: dispatch relay交易数量,
        ExecutionCount: 交易执行数量,
        ConsensusHeaderHash: consensus_header的哈希,
        ConfirmedTxnMerkle: 交易树树根,
        ChainStateMerkle": 状态改变树树根,
        Hash: 区块哈希,
        Height: 区块高度,
        Timestamp: 时间戳,
        Miner: 矿工,
        State: 区块状态,
        Transactions: 交易集合
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
        根据分片序号和区块哈希获取transaction block
    @params:
        shard_index:分片序号
        height: 高度
    @response -- object:
        同上
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
        根据交易哈希获取交易
    @params:
        hash:交易哈希
    @response -- object:
        Hash: 交易哈希,
        GasOffered: 交易的gaslimit,
        GasPrice": 交易的gasprice,
        Grouped: 是否是relay group类型,
        uTxnSize: 交易大小(Bytes),
        Mode:  类型,
        Function: 调用的合约函数,
        Input: 输入参数,
        Invocation: 调用信息
        Stage": 交易状态,
        Height: 交易所在区块高度,
        Shard: [交易所在分片,ShardOrder],
        ConfirmState: 交易状态
    """
    @exception_handler
    def get_transaction(self,hash:str,shard_index=None):
        method = "dx.transaction"
        params = {}
        params.update({"hash":hash})
        if shard_index is not None:
            params.update({"shard_index":shard_index})
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        合成交易,将交易的各字段合成成字节流形式,后续加入签名后发送到链上
    @params:
        sender: 发送者
        function: 调用的合约函数(<dapp>.<contract>.<function>)
        args: 函数调用参数,object
        isn: 交易isn,不填默认为最新isn,同以太坊nonce
        is_delegatee: 是否是委托交易
        gas_price: 设置交易gas_price
        gas_limit: 设置交易gas_limit
    @response -- bytes
        合成的交易base64编码
        
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
        本地构建交易,不依赖RPC调用,按照解析交易的相反逻辑实现
    @params:
        sender: 发送者地址或DioxAccount对象
        function: 调用的合约函数(<dapp>.<contract>.<function>)
        args: 函数调用参数,dict格式,key为参数名
        signature: 函数签名,格式如"address:to,uint32:amount",如果不提供则从合约信息中获取
        contract_info: 合约信息对象(可选),如果不提供则通过RPC获取
        isn: 交易isn,不填默认为最新isn
        is_delegatee: 是否是委托交易
        gas_price: 设置交易gas_price
        gas_limit: 设置交易gas_limit
        ttl: 交易生存时间
    @response -- bytes
        未签名的交易字节流
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
        发送签名后的交易
    @params:
        signed_txn: 签名后的交易字节流
        sync: 是否同步等待返回结果
        timeout: 超时时间
    @response -- str
        交易哈希(base32编码)
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
        根据合约名称获取合约详细信息(类似abi)
    @params:
        dapp_name: dapp名称
        contract_name: 合约名称
    @response -- object
        ContractID: 合约ID(唯一),
        ContractVersionID: 合约ID+合约版本号,
        Contract": 合约名称,
        Hash: 合约内容哈希值,
        ImplmentedInterfaces: 合约实现的接口,
        StateVariables: 合约变量([{'name':<变量名称>,'scope':<变量所属scope>,'dataType':<变量类型>}...]),
        Scopes: 合约中所有的scope,
        Interfaces: 合约定义的接口,
        Functions: 合约定义的所有函数
    """
    @exception_handler
    def get_contract_info(self,dapp_name,contract_name):
        method = "dx.contract_info"
        params = {"contract":"{}.{}".format(dapp_name,contract_name)}
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        查询已经部署的合约对应的代码
    @params:
        dapp_name: dapp名称
        contract_name: 合约名称
    @response -- str
        返回合约的源代码字符串
    """
    @exception_handler
    def get_source_code(self,dapp_name,contract_name):
        method = "dx.source_code"
        params = {"contract":"{}.{}".format(dapp_name,contract_name)}
        response = self.make_request(method,params)
        return response

    """
    @description:
        部署合约
    @params:
        dapp_name: dapp名称
        delegator: dapp的所有者,签名账户
        file_path: 合约文件路径,需要.prd文件
        source_code: 如果不指定合约文件路径则需要直接给出源码
        construct_args: 合约构造函数,object
        compile_time: 合约最长的编译时间,一般不设置
    @response -- str
        合约部署交易哈希
    """
    @exception_handler
    def deploy_contract(self,dapp_name,delegator:DioxAccount,file_path=None,source_code=None,construct_args:dict=None,compile_time=None):
        deploy_args={}
        if file_path is not None:
            with open(file_path) as f:
                deploy_args.update({"code":[f.read()]})
        else:
            if source_code is None:
                raise DioxError(-10001, "params error")
            else:
                deploy_args.update({"code":[source_code]})
        deploy_args.update({"cargs":[json.dumps(construct_args)]})
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
        批量部署合约
    @params:
        dapp_name: dapp名称
        delegator: dapp的所有者,签名账户
        contracts: 合约文件绝对路径和构造参数的映射字典, dict[绝对路径, 构造参数]
        compile_time: 合约最长的编译时间,一般不设置
    @response -- str
        合约部署交易哈希
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
        获取合约状态信息
    @params:
        contract_with_scope: 想要获取的状态变量scope,可选值有(global | shard | address | uint32 | uint64 | uint128 | uint256| uint512)
        scope_key: scope对应的key,比如scope是address,则该字段对应的是一个地址,如果是global,该字段为空
    @response -- object
        状态object
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
        获取dapp信息
    @params:
        dapp_name: dapp名称
    @response -- object
        DappID: dapp对应的dappid
    """
    @exception_handler
    def get_dapp_info(self,dapp_name):
        method = "dx.dapp"
        params = {"name":"{}".format(dapp_name)}
        response = self.make_request(method,params)
        return Box(response,default_box=True)

    """
    @description:
        获取token信息
    @params:
        token_symbol: token名称(全大写)
    @response -- object
        TokenId: Token对应的id
    """
    @exception_handler
    def get_token_info(self,token_symbol):
        method = "dx.token"
        params = {"symbol":"{}".format(token_symbol)}
        response = self.make_request(method,params)
        return Box(response,default_box=True)


    """
    @description:
        获取某笔交易中发出的event(relay@external交易)
    @params:
        txhash: 交易哈希
    @response -- object
        tx: relay@external对应的交易(里面的input字段需要自行反序列化)
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
        创建token
    @params:
        @Minter: 发币合约的CID,没有minter或者后续再设置minter填0
        @MinterFlags: 0-不允许该合约发币(临时性),1-允许该合约发币(临时性),2-不允许该合约发币(永久性),3-允许该合约发币(永久性)
        @TokenFlags: 0:可以后续设置minter,1不可以后续设置minter
        @Symbol: 代币名称,全大写,长度3-8
        @InitSupply:初始发行量
        @Deposit: 这个代币初始存入的dio数量
    @response -- object
        状态object
    @TBD.这些flag换成枚举变量
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

        function = tx.Function
        input_data = tx.Input

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

