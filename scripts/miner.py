from sanchain.core import SanchainCore
from sanchain.models import Block, Account
from sanchain.utils import CONFIG, SanchainConfig

import json


if __name__ == "__main__":
    core = SanchainCore.local('test-3')

    # New test
    # config = SanchainConfig.default()
    # config.update_local_config()
    # core = SanchainCore.new('test-3')

    miner_account = Account.from_json(
        json.load(open(CONFIG.DB_FOLDER / "accounts/account_4.json", "r")))

    for i in range(10):
        transactions = core.mempool.read_transactions()
        block = Block.new(transactions)
        block.mine(miner_account.public_key)
        core.add_block(block)

        for transaction in transaction:
            core.mempool.remove_transaction(transaction)

        CONFIG.update_wrt_recent_block(block)
        print(f"Block {block.idx} mined: {block.to_json()['hash']}")
