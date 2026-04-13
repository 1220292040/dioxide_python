import os


class Config:
    rpc_url = os.environ.get("DIOX_RPC_URL", "http://127.0.0.1:62222/api")
    log_dir = "logs"
    ws_rpc = os.environ.get("DIOX_WS_URL", "ws://127.0.0.1:62222/api")
    default_thread_nums = 32