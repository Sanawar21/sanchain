from sanchain.models import Transaction, Account, UTXO
from sanchain.utils import CONFIG
from sanchain.core import SanchainCore

import json


if __name__ == "__main__":
    core = SanchainCore.local('test')
    rich = Account.from_json(
        json.load(open(CONFIG.DB_FOLDER / "accounts/miner.json", "r")))
    poor_address = Account.from_json(
        json.load(open(CONFIG.DB_FOLDER / "accounts/account_4.json", "r"))).public_key

    txn = Transaction.unsigned(
        rich.public_key,
        poor_address,
        360.04,
        []
    )
    rich_utxos = core.utxo_set.fetch_by_owner(rich.verification_key)
    rich_utxos.sort(key=lambda x: x.value)
    # TODO: Implement a greedy algorithm
    to_use = []
    for utxo in rich_utxos:
        to_use.append(utxo)
        if sum([x.value for x in to_use]) >= txn.amount:
            break

    txn.utxos = to_use
    txn.sign(rich.private_key)
    core.mempool.add_transaction(txn)
