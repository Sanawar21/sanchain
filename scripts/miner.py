from sanchain.core import SanchainCore
from sanchain.models import Block, Account


if __name__ == "__main__":
    core = SanchainCore.local('test-5')

    # # New test
    # config = SanchainConfig.default()
    # config.update_local_config()
    # core = SanchainCore.new('test-4')

    miner_account = Account.from_json_path(
        core.config.DB_FOLDER / "accounts/account_4.json")

    # TODO: If a UTXO is not spent, remove transaction ID from it in the UTXO set

    for i in range(5):
        transactions = core.mempool.read_transactions()
        block = Block.new(transactions, core.config)
        block.mine(miner_account.public_key)
        core.add_block(block)

        for transaction in transactions:
            core.mempool.remove_transaction(transaction)

        core.config.update_wrt_recent_block(block)
        print(f"Block {block.idx} mined: {block.to_json()['hash']}")
