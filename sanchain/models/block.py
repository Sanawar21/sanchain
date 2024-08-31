import rsa

from .config import SanchainConfig
from .transaction import Transaction


class Block:
    def __init__(self, timestamp: int, merkle_root: bytes, config: SanchainConfig, transactions: list[Transaction]) -> None:
        self.index = config.last_block_index + 1
        self.timestamp = timestamp
        self.merkle_root = merkle_root
        self.config = config
        self.transactions = transactions

    def __calculate_merkle_root(self):
        for i in range(len(self.transactions), 2):
            pass

    def mine(self, miner: rsa.PublicKey):
        # verify and execute transactions
        for transaction in self.transactions:
            if transaction.verify():
                transaction.execute(miner)
            else:
                # invalid transaction
                pass  # TODO: remove from mempool so that it can't be mined again

        # calculate merkle hash
