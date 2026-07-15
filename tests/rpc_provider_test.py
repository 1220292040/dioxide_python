from dioxide_python_sdk.utils.rpc import HTTPProvide


def test_http_provider_request_state_is_isolated_per_client():
    first = HTTPProvide("http://127.0.0.1:1/api")
    second = HTTPProvide("http://127.0.0.1:2/api")
    try:
        first.encode_rpc_request("tx.compose", {"value": 1})
        second.encode_rpc_request("dx.overview", {})

        assert first.request_params == {"req": "tx.compose"}
        assert second.request_params == {"req": "dx.overview"}
        assert first.session is not second.session
    finally:
        first.session.close()
        second.session.close()
