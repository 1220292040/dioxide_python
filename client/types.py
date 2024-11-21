

from enum import Enum

GLOBAL_IDENTIFIER = 65535

class BlockState(Enum):
    DUS_RECEIVED = 0
    DUS_INVALID = 1
    DUS_EXCUTED = 2
    DUS_FORKED = 3
    DUS_FINALIZED = 4
    DUS_ARCHIVED = 5
    DUS_ARCHIVED_UNCLE = 6
    
class BlkCommitState(Enum):
	BLKCS_INIT = 0			    # init state
	BLKCS_PENDING_BLOCKID = 1		# parent available but no sufficient block id
	BLKCS_PENDING_COMMIT = 2		# linked on block tree, rooted by chain base, but lacking uncle
	BLKCS_PENDING_SHARD_COMMIT = 3	# Global TB is confirmed and waits for shards on-duty (this is for master block only)
	BLKCS_CONFIRMED = 4		# transaction/uncle are all resolved, txn executed, state updated. i.e. committed
	BLKCS_IGNORED = 5			# ready to commit, but the block is finalized as forked
	BLKCS_COMMIT_ERROR = 6		# incorrect block body, commit failed, while its block header still counts
	BLKCS_REBASING = 7				# mark to be removed, when preforming rebase


class BlkFinalityState(Enum):
	BLKFS_NONE = 0			    # yet finalized
	BLKFS_FINALIZED = 1		# finalized as head chain, will not be other's uncle and children locked
	BLKFS_UNCLED = 2			# finalized as forked chain, and is uncle of any finalized block
	BLKFS_ORPHANED = 3			# finalized as forked chain, and is none's uncle


class BlkArchiveState(Enum):
	BLKAS_NONE = 0
	BLKAS_DISCARD = 1			# for orphaned
	BLKAS_ARCHIVING = 2		# block is added to archive queue
	BLKAS_ARCHIVED = 3			# all data of the block (body, txn, txnids) are saved to db, for uncle only body is saved


class TxnConfirmState(Enum):
	TXN_RELAY_INVALIDED = -3		# when its originate block is forked
	TXN_READY = 0					# ready to be confirmed (forward broadcast allowed since then)
	TXN_CONFIRMED = 1				# at least one block confirmed the txn, which enters MemoryPool::_TxnConfirmedMap
	TXN_FINALIZED = 2				# confirmed by a block which is finalized
	TXN_ABORTED = 3				# duplicated ISN that another one is confirmed and finalized (normal txn only)
	TXN_EXPIRED = 4				# when its expiration time < latest finalized block time (normal txn only)
	TXN_ARCHIVED = 5				# saved to DB after TXN_FINALIZED


TXN_CONFIRMED_STATUS = [TxnConfirmState.TXN_ARCHIVED.name,TxnConfirmState.TXN_CONFIRMED.name,TxnConfirmState.TXN_FINALIZED.name]
TXN_FINALIZED_STATUS = [TxnConfirmState.TXN_ARCHIVED.name,TxnConfirmState.TXN_FINALIZED.name]
TXN_ARCHIVED_STATUS = [TxnConfirmState.TXN_ARCHIVED.name]
