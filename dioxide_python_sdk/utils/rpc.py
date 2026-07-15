
from ..client.stat import StatTool
import logging
import json
import requests

class HTTPProvide:
    logger = logging.getLogger("client.providers.HTTPProvider")
    def __init__(self,url=None,kwargs=None):
        # Request parameters are mutable and must be isolated per client. A class-level
        # dictionary makes concurrent clients overwrite each other's ``req`` method.
        self.request_params = {}
        if url is None:
            self.url = "http://127.0.0.1:45678/api"
        else:
            self.url = url
        self.request_kwargs = kwargs or {}
        self.session = requests.Session()
    
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

        raw_response = self.session.post(
            self.url,
            params=self.request_params,
            data=request_data,
            **self.request_kwargs
        )
        response = self.decode_rpc_response(raw_response)
        stat.done()
        stat.debug("make_request:{},sendbytes:{}".format(method,len(request_data)) )
        self.logger.debug("[response::%s], data: %s",
                           method, response)
        return response
