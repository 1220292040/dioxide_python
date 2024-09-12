
from client.stat import StatTool
import logging
import json
from utils.request import make_post_request

class HTTPProvide:
    logger = logging.getLogger("client.providers.HTTPProvider")
    request_params = {}
    request_kwargs = None
    def __init__(self,url=None,kwargs=None):
        if url is None:
            self.url = "http://127.0.0.1:62222/api"
        else:
            self.url = url
        self.request_kwargs = kwargs or {}
    
    def encode_rpc_request(self,method,params):
        self.request_params.update({"req":method})
        return json.dumps(params or {})

    def decode_rpc_response(self,response):
        return response.json()

    def make_request(self, method, params):
        request_data = self.encode_rpc_request(method, params)
        stat = StatTool.begin()
        self.logger.debug("[request::%s,%s], data: %s",
                          self.url, method,request_data)

        raw_response = make_post_request(
            self.url,
            self.request_params,
            request_data,
            **self.request_kwargs
        )
        response = self.decode_rpc_response(raw_response)
        stat.done()
        stat.debug("make_request:{},sendbytes:{}".format(method,len(request_data)) )
        self.logger.debug("[response::%s], data: %s",
                           method, response)
        return response