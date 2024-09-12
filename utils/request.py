import requests

def make_post_request(url,params,data,**kwargs):
    kwargs.setdefault('timeout',10)
    response = requests.post(url,params=params,data=data, **kwargs)
    response.raise_for_status()
    return response
