import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, ".")

from dioxide_python_sdk.client.dioxclient import DioxClient
from dioxide_python_sdk.client.types import PenaltyEvidenceReason


class TestConsensusIncentiveQueries(unittest.TestCase):
    def setUp(self):
        self.client = DioxClient()

    @patch.object(DioxClient, "make_request")
    def test_get_consensus_incentive_uses_direct_rpc_action(self, mock_make_request):
        mock_make_request.return_value = {
            "BaseBlockReward": "0",
            "CrossShardRewardPool": "0",
            "RewardAdjustAlpha": 250000,
            "RewardConcentrationLambda": 0,
            "PenaltyMaxFine": "0",
            "PenaltyReserve": "0",
            "RewardReserve": "0",
            "DynamicRewardTxLoadPpm": 10000,
            "DynamicRewardRelayLoadPpm": 50000,
            "DynamicRewardGasLoadPpm": 100000,
            "DynamicRewardMaxMultiplierPpm": 2000000,
            "RewardRatioDenominator": 1000000,
        }

        result = self.client.get_consensus_incentive()

        mock_make_request.assert_called_once_with(
            "dx.consensus_incentive",
            {},
        )
        self.assertEqual(result.RewardAdjustAlpha, 250000)
        self.assertEqual(result.DynamicRewardTxLoadPpm, 10000)
        self.assertEqual(result.DynamicRewardMaxMultiplierPpm, 2000000)
        self.assertEqual(result.RewardRatioDenominator, 1000000)

    @patch.object(DioxClient, "make_request")
    def test_get_chain_info_maps_overview_height(self, mock_make_request):
        mock_make_request.return_value = {
            "HeadHeight": 123,
            "HeadHash": "abc",
        }

        result = self.client.get_chain_info()

        mock_make_request.assert_called_once_with("dx.overview", {})
        self.assertEqual(result.HeadHeight, 123)
        self.assertEqual(result.Height, 123)

    @patch.object(DioxClient, "make_request")
    def test_get_consensus_fee_attribution_uses_direct_rpc_action(self, mock_make_request):
        mock_make_request.return_value = {
            "SourceHeight": 20,
            "SourceRelayCount": 3,
            "AttributionSource": 1,
            "SourceGasFee": "100",
            "GasReward": "80",
            "CrossShardPoolContribution": "20",
            "CrossShardReward": "20",
        }

        result = self.client.get_consensus_fee_attribution()

        mock_make_request.assert_called_once_with(
            "dx.consensus_fee_attribution",
            {},
        )
        self.assertEqual(result.SourceHeight, 20)
        self.assertEqual(result.SourceRelayCount, 3)
        self.assertEqual(result.AttributionSource, 1)
        self.assertEqual(result.SourceGasFee, "100")
        self.assertEqual(result.GasReward, "80")
        self.assertEqual(result.CrossShardPoolContribution, "20")
        self.assertEqual(result.CrossShardReward, "20")

    @patch.object(DioxClient, "make_request")
    def test_get_miner_stats_uses_direct_rpc_action(self, mock_make_request):
        mock_make_request.return_value = {
            "LastMined": 10,
            "MinedCount": 2,
            "CrossShardVerifiedCount": 3,
            "CrossShardVerifiedWeight": "4",
            "LastActiveHeight": 21,
            "OfflineStage": 1,
            "TotalReward": "100",
            "TotalBaseReward": "75",
            "TotalGasReward": "20",
            "TotalCrossShardReward": "5",
            "TotalPenalty": "0",
            "InefficientRounds": 0,
        }

        result = self.client.get_miner_stats("dio1miner")

        mock_make_request.assert_called_once_with(
            "dx.miner_stats",
            {"address": "dio1miner"},
        )
        self.assertEqual(result.MinedCount, 2)
        self.assertEqual(result.TotalReward, "100")
        self.assertEqual(result.TotalBaseReward, "75")
        self.assertEqual(result.TotalGasReward, "20")
        self.assertEqual(result.TotalCrossShardReward, "5")
        self.assertEqual(result.CrossShardVerifiedCount, 3)
        self.assertEqual(result.CrossShardVerifiedWeight, "4")
        self.assertEqual(result.LastActiveHeight, 21)
        self.assertEqual(result.OfflineStage, 1)

    @patch.object(DioxClient, "make_request")
    def test_get_staking_info_uses_direct_rpc_action(self, mock_make_request):
        mock_make_request.return_value = {
            "Amount": "1000",
            "StartTime": "12",
            "UnlockAmount": "300",
            "UnlockHeight": 45,
            "PendingPenalty": "0",
        }

        result = self.client.get_staking_info("dio1staker")

        mock_make_request.assert_called_once_with(
            "dx.staking_info",
            {"address": "dio1staker"},
        )
        self.assertEqual(result.UnlockAmount, "300")
        self.assertEqual(result.UnlockHeight, 45)
        self.assertEqual(result.PendingPenalty, "0")

    @patch.object(DioxClient, "make_request")
    def test_get_consensus_penalty_uses_direct_rpc_action(self, mock_make_request):
        mock_make_request.return_value = {
            "PendingPenalty": "300",
            "EvidenceHash": "0xabc",
            "EvidenceStatus": 1,
            "ResponsibleMiner": "dio1miner",
            "EvidenceObjectType": 1,
            "EvidenceObjectHeight": 18,
            "EvidenceObjectShard": 65535,
            "EvidenceObjectResponsibleMiner": "dio1miner",
            "EvidenceReason": 1,
            "EvidenceProofSummaryHash": "0xabc",
            "EvidenceSubjectHeight": 18,
            "EvidenceSubjectShard": 65535,
            "ReviewAmount": "300",
            "ReviewStartHeight": 20,
            "ReviewEndHeight": 20,
            "EvidenceType": 1,
            "PenaltyReserve": "100",
            "PenaltyMaxFine": "500",
        }

        result = self.client.get_consensus_penalty("dio1miner")

        mock_make_request.assert_called_once_with(
            "dx.consensus_penalty",
            {"address": "dio1miner"},
        )
        self.assertEqual(result.PendingPenalty, "300")
        self.assertEqual(result.PenaltyReserve, "100")
        self.assertEqual(result.EvidenceHash, "0xabc")
        self.assertEqual(result.EvidenceStatus, 1)
        self.assertEqual(result.ResponsibleMiner, "dio1miner")
        self.assertEqual(result.EvidenceObjectType, 1)
        self.assertEqual(result.EvidenceObjectHeight, 18)
        self.assertEqual(result.EvidenceObjectShard, 65535)
        self.assertEqual(result.EvidenceObjectResponsibleMiner, "dio1miner")
        self.assertEqual(result.EvidenceReason, 1)
        self.assertEqual(result.EvidenceProofSummaryHash, "0xabc")
        self.assertEqual(result.EvidenceSubjectHeight, 18)
        self.assertEqual(result.EvidenceSubjectShard, 65535)
        self.assertEqual(result.ReviewAmount, "300")
        self.assertEqual(result.ReviewStartHeight, 20)
        self.assertEqual(result.ReviewEndHeight, 20)
        self.assertEqual(result.EvidenceType, 1)

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_pending_penalty_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_pending_penalty(
            user=user,
            miner="dio1miner",
            amount=300,
            evidence_hash="abc123",
            reason=2,
            sync=False,
            timeout=7,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_pending_penalty",
            args={
                "Miner": "dio1miner",
                "Amount": "300",
                "EvidenceHash": "abc123",
                "Reason": 2,
            },
            is_sync=False,
            timeout=7,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_pending_penalty_accepts_tamper_reason_enum(self, mock_send_transaction):
        # design_spec 2.4: cross-shard tamper -> full stake slash.
        # The enum member must serialize to Reason=4 in the transaction args.
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_pending_penalty(
            user=user,
            miner="dio1miner",
            amount=300,
            evidence_hash="abc123",
            reason=PenaltyEvidenceReason.CROSS_SHARD_MESSAGE_TAMPER,
            sync=False,
            timeout=7,
        )

        self.assertEqual(result, "txhash")
        self.assertEqual(PenaltyEvidenceReason.CROSS_SHARD_MESSAGE_TAMPER.value, 4)
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_pending_penalty",
            args={
                "Miner": "dio1miner",
                "Amount": "300",
                "EvidenceHash": "abc123",
                "Reason": 4,
            },
            is_sync=False,
            timeout=7,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_penalty_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_penalty(
            user=user,
            miner="dio1miner",
            amount="400",
            evidence_hash="def456",
            sync=True,
            timeout=9,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_penalty",
            args={
                "Miner": "dio1miner",
                "Amount": "400",
                "EvidenceHash": "def456",
            },
            is_sync=True,
            timeout=9,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_penalty_reject_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_penalty_reject(
            user=user,
            evidence_hash="def456",
            sync=False,
            timeout=10,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_penalty_reject",
            args={
                "EvidenceHash": "def456",
            },
            is_sync=False,
            timeout=10,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_penalty_expire_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_penalty_expire(
            user=user,
            miner="dio1miner",
            evidence_hash="abc789",
            sync=True,
            timeout=12,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_penalty_expire",
            args={
                "Miner": "dio1miner",
                "EvidenceHash": "abc789",
            },
            is_sync=True,
            timeout=12,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_penalty_appeal_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_penalty_appeal(
            user=user,
            miner="dio1miner",
            evidence_hash="abc999",
            sync=False,
            timeout=14,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_penalty_appeal",
            args={
                "Miner": "dio1miner",
                "EvidenceHash": "abc999",
            },
            is_sync=False,
            timeout=14,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_penalty_appeal_resolve_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_penalty_appeal_resolve(
            user=user,
            miner="dio1miner",
            evidence_hash="abc111",
            restore=True,
            sync=True,
            timeout=15,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_penalty_appeal_resolve",
            args={
                "Miner": "dio1miner",
                "EvidenceHash": "abc111",
                "Restore": True,
            },
            is_sync=True,
            timeout=15,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_consensus_inefficient_penalty_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.consensus_inefficient_penalty(
            user=user,
            miner="dio1miner",
            amount=100,
            inefficient_round_delta=2,
            evidence_hash="feed",
            sync=False,
            timeout=11,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.consensus_inefficient_penalty",
            args={
                "Miner": "dio1miner",
                "Amount": "100",
                "InefficientRoundDelta": 2,
                "EvidenceHash": "feed",
            },
            is_sync=False,
            timeout=11,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_staking_unlock_request_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.staking_unlock_request(
            user=user,
            staker="dio1staker",
            amount=200,
            unlock_height=55,
            sync=False,
            timeout=13,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.unlock_request",
            args={
                "Staker": "dio1staker",
                "Amount": "200",
                "UnlockHeight": 55,
            },
            is_sync=False,
            timeout=13,
        )

    @patch.object(DioxClient, "send_transaction")
    def test_staking_release_uses_core_coin_transaction(self, mock_send_transaction):
        user = object()
        mock_send_transaction.return_value = "txhash"

        result = self.client.staking_release(
            user=user,
            staker="dio1staker",
            sync=True,
            timeout=17,
        )

        self.assertEqual(result, "txhash")
        mock_send_transaction.assert_called_once_with(
            user=user,
            function="core.coin.release",
            args={
                "Staker": "dio1staker",
            },
            is_sync=True,
            timeout=17,
        )


if __name__ == "__main__":
    unittest.main()
