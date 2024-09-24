from sanchain.models import Transaction, Account, UTXO
from sanchain.core import SanchainCore


# 5 has 1000, he sends 345 to 2 and 466 to 4 and 5 mine the new block

if __name__ == "__main__":
    sender = "3"
    receiver = "5"
    amount = 10

    core = SanchainCore.local('test-5')

    rich = Account.from_json_path(
        (core.config.DB_FOLDER / f"accounts/account_{sender}.json"))
    poor_address = Account.from_json_path(
        (core.config.DB_FOLDER / f"accounts/account_{receiver}.json")).public_key

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

    # TODO: Why are the current transactions not being mined?
