from sanchain.core import SanchainCore
from sanchain.models import Block, Account
from sanchain.utils import CONFIG

import json

# TODO: Refresh config before using it everytime. Or create a new object of config everytime.
#       instead of using the utils one

if __name__ == "__main__":
    core = SanchainCore.local('test-2')
    # core = SanchainCore.new('test-2')
    miner_account = Account.from_json(
        json.load(open(CONFIG.DB_FOLDER / "accounts/account_5.json", "r")))

    while True:
        transactions = core.mempool.read_transactions()
        block = Block.new(transactions)
        block.mine(miner_account.public_key)
        core.add_block(block)
        CONFIG.update_wrt_recent_block(block)
        print(f"Block {block.idx} mined: {block.to_json()['hash']}")
