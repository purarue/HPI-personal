"""
Gets Transactions/Historical account balance (banking/finances) using
https://github.com/seanbreckenridge/mint
"""

import os
import logging
from typing import Tuple, List
from functools import lru_cache

import budget
from budget import analyze
from more_itertools import last

from my.core import Stats
from my.core.logging import mklevel


@lru_cache(1)
def _data() -> Tuple[List[analyze.Snapshot], List[analyze.Transaction]]:
    """
    Get data from the budget module (data is handled by that/environment variables)
    see https://github.com/seanbreckenridge/mint
    """
    debug: bool = False
    if "HPI_LOGS" in os.environ:
        if mklevel(os.environ["HPI_LOGS"]) == logging.DEBUG:
            debug = True
    return budget.data(debug=debug)


def _all_balances() -> List[analyze.Snapshot]:
    """
    Return all the balance snapshots, tracked in the git hitsory
    """
    bal_snapshots, _ = _data()
    bal_snapshots.sort(key=lambda t: t.at)
    return list(analyze.cleaned_snapshots(sorted_snapshots=bal_snapshots))


def balance() -> analyze.Snapshot:
    """
    Return my current account balance
    """
    return last(_all_balances())


def transactions() -> List[analyze.Transaction]:
    """
    Return all transactions (me buying things) I've made. Merges data from all of my different bank accounts
    """
    _, transactions = _data()
    transactions.sort(key=lambda t: t.on)
    return transactions


def stats() -> Stats:
    from my.core import stat

    return {
        **stat(_all_balances),
        **stat(transactions),
    }
