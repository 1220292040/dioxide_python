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
    @exception_handler
    def get_overview(self):
        return self.make_request("dx.overview",{})
    
    @exception_handler
    def get_block_number(self):
        respone = self.make_request("dx.committed_head_height",{})
        return int(respone["HeadHeight"])

    @exception_handler
    def get_shard_index(self,scope,scope_key):
        method = "dx.shard_index"
        params = {}
        params.update({"scope":scope})
        params.update({"scope_key":scope_key})
        response = self.make_request(method,params)
        return int(response["ShardIndex"])

    @exception_handler
    def get_isn(self,address):
        method = "dx.isn"
        params = {}
        params.update({"address":address})
        response = self.make_request(method,params)
        return int(response["ISN"])

    @exception_handler
    def get_consensus_header_by_height(self,height):
        method = "dx.consensus_header"
        params = {}
        params.update({"query_type":0})
        params.update({"height":height})
        response = self.make_request(method,params)
        return AttributeDict(response)

    @exception_handler
    def get_consensus_header_by_hash(self,hash:str):
        method = "dx.consensus_header"
        params = {}
        params.update({"query_type":1})
        params.update({"hash":hash})
        response = self.make_request(method,params)
        return AttributeDict(response)

    @exception_handler
    def get_transaction_block_by_height(self,shard_index,height):
        method = "dx.transaction_block"
        params = {}
        params.update({"query_type":0})
        params.update({"shard_index":shard_index})
        params.update({"height":height})
        response = self.make_request(method,params)
        return AttributeDict(response)

    @exception_handler
    def get_transaction_block_by_hash(self,shard_index,hash:str):
        method = "dx.transaction_block"
        params = {}
        params.update({"query_type":1})
        params.update({"shard_index":shard_index})
        params.update({"hash":hash})
        response = self.make_request(method,params)
        return AttributeDict(response)
    
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