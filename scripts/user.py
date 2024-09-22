from sanchain.models import Transaction, Account, UTXO
from sanchain.utils import CONFIG
from sanchain.core import SanchainCore

import json

# 5 has 1000, he sends 345 to 2 and 466 to 4 and 5 mine the new block

if __name__ == "__main__":
    sender = 5
    receiver = 2
    amount = 345

    core = SanchainCore.local('test-3')

    rich = Account.from_json(
        json.load(open(CONFIG.DB_FOLDER / f"accounts/account_{sender}.json", "r")))
    poor_address = Account.from_json(
        json.load(open(CONFIG.DB_FOLDER / f"accounts/account_{receiver}.json", "r"))).public_key

    txn = Transaction.unsigned(
        rich.public_key,
        poor_address,
        amount,
        []
    )
    rich_utxos = core.utxo_set.fetch_by_owner(
        rich.verification_key, unused=True)
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
