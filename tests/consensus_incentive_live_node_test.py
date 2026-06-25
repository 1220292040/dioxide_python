import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, ".")

from dioxide_python_sdk.client.dioxclient import DioxClient


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _resolve_diox_binary():
    explicit = os.environ.get("DIOX_NODE_BIN")
    if explicit:
        return Path(explicit)

    repo = Path(os.environ.get("OXD_BC_DIR", "/home/lsl/github/idea/oxd_bc"))
    return repo / "bin" / "bin_debug" / "diox"


@pytest.fixture(scope="module")
def consensus_node(tmp_path_factory):
    diox_bin = _resolve_diox_binary()
    if not diox_bin.exists():
        pytest.skip(f"diox binary not found: {diox_bin}")

    port = _find_free_port()
    datadir = tmp_path_factory.mktemp("diox_consensus_node")
    log_path = datadir / "node.log"
    cmd = [
        str(diox_bin),
        "-nuke",
        "-mine",
        "-api_test",
        f"-datadir:{datadir}",
        f"-api:127.0.0.1:{port}",
    ]

    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=str(diox_bin.parents[2]),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

    client = DioxClient(url=f"http://127.0.0.1:{port}/api")
    deadline = time.time() + 45
    last_error = None
    while time.time() < deadline:
        if proc.poll() is not None:
            log_tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            pytest.fail(f"diox node exited before readiness, code={proc.returncode}\n{log_tail}")
        try:
            overview = client.get_chain_info()
            height = int(getattr(overview, "Height", 0) or getattr(overview, "HeadHeight", 0) or 0)
            if height > 0:
                yield client
                break
        except Exception as exc:
            last_error = exc
        time.sleep(1)
    else:
        log_tail = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
        pytest.fail(f"diox node did not reach block height before timeout: {last_error}\n{log_tail}")

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)

    shutil.rmtree(datadir, ignore_errors=True)


def test_consensus_incentive_queries_against_started_node(consensus_node):
    overview = consensus_node.get_chain_info()
    height = int(getattr(overview, "Height", 0) or getattr(overview, "HeadHeight", 0) or 0)
    assert height > 0
    latest_header = consensus_node.get_consensus_header_by_height(height)
    miner_address = getattr(latest_header, "Miner", None)
    assert miner_address

    incentive = consensus_node.get_consensus_incentive()
    assert hasattr(incentive, "CrossShardRewardPool")
    assert hasattr(incentive, "PenaltyReserve")
    assert hasattr(incentive, "RewardRatioDenominator")

    fee_attribution = consensus_node.get_consensus_fee_attribution()
    assert hasattr(fee_attribution, "SourceHeight")
    assert hasattr(fee_attribution, "SourceRelayCount")
    assert hasattr(fee_attribution, "AttributionSource")
    assert hasattr(fee_attribution, "SourceGasFee")
    assert hasattr(fee_attribution, "GasReward")
    assert hasattr(fee_attribution, "CrossShardPoolContribution")
    assert hasattr(fee_attribution, "CrossShardReward")

    miner_stats = consensus_node.get_miner_stats(miner_address)
    assert hasattr(miner_stats, "CrossShardVerifiedCount")
    assert hasattr(miner_stats, "CrossShardVerifiedWeight")
    assert hasattr(miner_stats, "TotalCrossShardReward")
    assert hasattr(miner_stats, "LastActiveHeight")
    assert hasattr(miner_stats, "OfflineStage")

    penalty = consensus_node.get_consensus_penalty(miner_address)
    assert hasattr(penalty, "EvidenceObjectType")
    assert hasattr(penalty, "EvidenceObjectHeight")
    assert hasattr(penalty, "EvidenceObjectShard")
    assert hasattr(penalty, "EvidenceObjectResponsibleMiner")
    assert hasattr(penalty, "EvidenceReason")
    assert hasattr(penalty, "EvidenceProofSummaryHash")
    assert hasattr(penalty, "EvidenceSubjectHeight")
    assert hasattr(penalty, "EvidenceSubjectShard")
