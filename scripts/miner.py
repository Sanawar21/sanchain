from sanchain.core import SanchainCore
from sanchain.models import Account


if __name__ == "__main__":
    core = SanchainCore.local('test-5')
    miner_account = Account.from_json_path("data/accounts/account_5.json")

    # TODO: If a UTXO is not spent, remove transaction ID from it in the UTXO set

    for i in range(5):
        block = core.create_block()
        block.mine(miner_account.public_key)
        core.add_block(block)

        for transaction in block.transactions:
            core.mempool.remove_transaction(transaction)

        # for transaction in block.invalid_transactions:
        #     core.free_transaction_utxos(transaction)
        #     core.mempool.remove_transaction(transaction)

        print(f"Block {block.idx} mined: {block.to_json()['hash']}")
