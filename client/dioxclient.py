"""
  dioxclientpy is a python client for dioxide node.
  @author: long
  @date: 2024-09-12
"""  
from client import clientlogger
from client.stat import StatTool
from client_config import Config
from utils.rpc import HTTPProvide
from client.account import DioxAccount,DioxAddress,DioxAddressType
from utils.gadget import exception_handler,get_subscribe_message
from attributedict.collections import AttributeDict
import base64
import time
import json
from client.contract import Scope
import os,threading
import websockets
from concurrent.futures import ThreadPoolExecutor
import asyncio


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

    def __init__(self):
        self.rpc = HTTPProvide(url=Config.rpc_url)
        self.rpc.logger = self.logger
        self.ws_rpc = Config.ws_rpc
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
        if response == None:
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
        Shard: array - per shard 信息
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
        return AttributeDict(response)

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
        return AttributeDict(response)

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
        return AttributeDict(response)

    """
    @description:
        根据分片序号和区块哈希获取transaction block
    @params:
        shard_index:分片序号
        height: 高度
    @response:
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
        return AttributeDict(response)
    
    """
    @description:
        根据交易哈希获取交易
    @params:
        hash:交易哈希
    @response:
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
        return AttributeDict(response)
    
    @exception_handler
    def compose_transaction(self,sender,function:str,args:dict,tokens:list=None,isn=None,is_delegatee=False,gas_price=None,gas_limit=None):
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
        print(params)
        response = self.make_request(method,params)
        return base64.b64decode(response["TxData"])

    @exception_handler
    def send_raw_transaction(self,signed_txn:bytes,sync=False,timeout=10):
        method = "tx.send"
        params = {"txdata":base64.b64encode(signed_txn).decode()}
        response = self.make_request(method,params)
        tx_hash = response["Hash"]
        if sync:
            now = time.time()
            while int(time.time()-now)<timeout:
                tx = self.get_transaction(tx_hash)
                if tx.ConfirmState != "TXN_READY":
                    return tx_hash
                time.sleep(1)
            raise DioxError(-10000, "timeout")
        return tx_hash


    @exception_handler
    def get_contract_info(self,dapp,contract_name):
        method = "dx.contract_info"
        params = {"contract":"{}.{}".format(dapp,contract_name)}
        response = self.make_request(method,params)
        return AttributeDict(response)

    @exception_handler
    def deploy_contract(self,dapp_name,delegatee:DioxAccount,file_path=None,source_code=None,construct_args:dict=None,timeout=None,sync=False):
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
        if timeout is not None:
            deploy_args.update({"timeout":timeout})
        dapp_address = DioxAddress(None,DioxAddressType.DAPP)
        dapp_address.set_delegatee_from_string(dapp_name)
        deployed_txn = self.compose_transaction(
            sender=dapp_address,
            function="core.delegation.deploy_contracts",
            args=deploy_args,
            is_delegatee=True
        )
        tx_hash = self.send_raw_transaction(delegatee.sign_diox_transaction(deployed_txn))
        return tx_hash
    
    @exception_handler
    def deploy_contracts(self,dapp_name,delegatee:DioxAccount,dir_path=None,suffix=".prd",construct_args:list[dict]=None,timeout=None,sync=False):
        deploy_args={}
        codes = []
        cargs = []
        print(dir_path)
        for filepath,_,filenames in os.walk(dir_path):
            for filename in filenames:
                if os.path.splitext(filename)[-1] == suffix:
                    with open(os.path.join(filepath,filename)) as f:
                        codes.append(f.read())
        for carg in construct_args:
            if carg is None:
                cargs.append("")
            else:
                cargs.append(json.dumps(carg))
        deploy_args.update({"code":codes})
        deploy_args.update({"cargs":cargs})
        if timeout is not None:
            deploy_args.update({"timeout":timeout})
        dapp_address = DioxAddress(None,DioxAddressType.DAPP)
        dapp_address.set_delegatee_from_string(dapp_name)
        deployed_txn = self.compose_transaction(
            sender=dapp_address,
            function="core.delegation.deploy_contracts",
            args=deploy_args,
            is_delegatee=True
        )
        tx_hash = self.send_raw_transaction(delegatee.sign_diox_transaction(deployed_txn))
        return tx_hash

    @exception_handler
    def get_contract_state(self,dapp,contract_name,scope:Scope,key):
        method = "dx.contract_state"
        params = {"contract_with_scope":str(dapp)+"."+str(contract_name)+"."+scope.name.lower()}
        if scope.value != scope.Global:
            params.update({"scope_key":key})
        response = self.make_request(method,params)
        return AttributeDict(response)

    @exception_handler
    def get_dapp_info(self,dapp_name):
        method = "dx.dapp"
        params = {"name":"{}".format(dapp_name)}
        response = self.make_request(method,params)
        return AttributeDict(response)

    #if overflow tcp buffer, consider use message queue
    @exception_handler
    def subscribe(self,topic:str,handler,filter=None):
        thread_id = threading.get_ident()
        asyncio.set_event_loop(self.loop)
        asyncio.run_coroutine_threadsafe(self.__subscribe(topic,thread_id, handler, filter),self.loop)

    @exception_handler
    def unsubscribe(self,thread_id):
        ws = self.ws_connections.get(thread_id)
        if ws is not None:
            asyncio.run_coroutine_threadsafe(self.__unsubscribe(ws, thread_id),self.loop)

    async def __subscribe(self,topic:str,thread_id,handler,filter=None):
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
    def wait_success(self,type:str,token:str,timeout = 10):
        now = time.time()
        if type == "dapp":
            while int(time.time()-now)<timeout:
                if self.get_dapp_info(token) is not None:
                    return True
                time.sleep(1)
            return False
        elif type == "contract":
            while int(time.time()-now)<timeout:
                if self.get_contract_info(token) is not None:
                    return True
                time.sleep(1)
            return False
        else:
            return True

    @exception_handler
    def send_transaction(self,user:DioxAccount,function:str,args:dict,tokens:list=None,isn=None,is_delegatee=False,gas_price=None,gas_limit=None,is_sync=True):
        unsigned_txn = self.compose_transaction(sender=user.address,
                                          function=function,
                                          args=args
                                        )
        signed_txn = user.sign_diox_transaction(unsigned_txn)
        tx_hash = self.send_raw_transaction(signed_txn,is_sync)
        return tx_hash
    
    @exception_handler
    def mint_dio(self,user:DioxAccount,amount,sync=True):
        tx_hash = self.send_transaction(user=user,function="core.coin.mint",args={"Amount":"{}".format(amount)},is_sync=sync)
        return tx_hash

    @exception_handler
    def create_dapp(self,user:DioxAccount,dapp_name,deposit_amount,sync=True):
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
        ok = self.wait_success("dapp",dapp_name)
        return tx_hash,ok