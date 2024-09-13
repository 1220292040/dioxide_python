"""
  dioxclientpy is a python client for dioxide node.
  @author: long
  @date: 2024-09-12
"""  
from client import clientlogger
from client.stat import StatTool
from client_config import Config
from utils.rpc import HTTPProvide
from client.dioxaccount import DioxAccount
from utils.gadget import exception_handler

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

    def __init__(self):
        self.rpc = HTTPProvide(url=Config.rpc_url)
        self.rpc.logger = self.logger

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
            e = DioxError(-1, None, "response is None")
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
        return respone["HeadHeight"]

    @exception_handler
    def get_shard_index(self,scope,scope_key):
        method = "dx.shard_index"
        params = {}
        params.update({"scope":scope})
        params.update({"scope_key":scope_key})
        response = self.make_request(method,params)
        return response["ShardIndex"]

    def get_consensus_header_by_height(self):
        pass

    def get_consensus_header_by_hash(self):
        pass

    def get_transaction_block_by_height(self):
        pass

    def get_transaction_block_by_hash(self):
        pass
    
    def get_transaction(self):
        pass 

    def send_raw_transaction(self):
        pass

    def deploy_contract(self):
        pass
    
    def get_contract_state(self):
        pass

    def get_contract_info(self):
        pass

    def subscribe(self):
        pass

    def unsubscribe(self):
        pass
