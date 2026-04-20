import os
import socket
import sys
from urllib.parse import urlparse

import pytest

sys.path.append(".")

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import GLOBAL_IDENTIFIER


def _rpc_available(url: str, timeout: float = 0.5) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _rpc_available(os.environ.get("DIOX_RPC_URL", "http://127.0.0.1:45678/api")),
    reason="Block smoke test requires a running DIOX RPC",
)


def test_block_queries_smoke():
    client = DioxClient()
    cur_height = client.get_block_number()
    assert cur_height is not None

    cur_consensus_header = client.get_consensus_header_by_height(cur_height)
    assert cur_consensus_header is not None

    if hasattr(cur_consensus_header, "Hash") and cur_consensus_header.Hash:
        cur_consensus_header_by_hash = client.get_consensus_header_by_hash(cur_consensus_header.Hash)
        assert cur_consensus_header_by_hash is not None

    g_transaction_block = client.get_transaction_block_by_height(GLOBAL_IDENTIFIER, cur_height)
    assert g_transaction_block is not None

    transaction_block_0 = client.get_transaction_block_by_height(0, cur_height)
    assert transaction_block_0 is not None

    if hasattr(g_transaction_block, "Hash") and g_transaction_block.Hash:
        g_transaction_block_by_hash = client.get_transaction_block_by_hash(
            GLOBAL_IDENTIFIER, g_transaction_block.Hash
        )
        assert g_transaction_block_by_hash is not None
