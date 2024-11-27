"""
Parses albums from my google sheet
https://github.com/purarue/albums
https://purarue.xyz/s/albums
"""

from dataclasses import dataclass

# see https://github.com/purarue/dotfiles/blob/master/.config/my/my/config/__init__.py for an example
from my.config import nextalbums as user_config  # type: ignore[attr-defined]
from my.core import Paths


@dataclass
class config(user_config):
    # path[s]/glob to the exported data. Resulting file from 'nextalbums export'
    export_path: Paths


from pathlib import Path
from typing import Iterator, Callable

from nextalbums.export import Album, read_dump
from my.core import get_files, Stats


# should only ever be one dump, the .job overwrites the file
def input() -> Path:
    dumps = list(get_files(config.export_path))
    dumps.sort(key=lambda p: p.stat().st_mtime)
    latest = dumps[-1]
    return latest


def _albums() -> Iterator[Album]:
    yield from read_dump(input())


def history() -> Iterator[Album]:
    """Only return items I've listened to, where the score is not null"""
    yield from filter(lambda a: a.listened, _albums())


def to_listen() -> Iterator[Album]:
    """Albums I have yet to listen to"""
    yield from filter(lambda a: not a.listened and not a.dropped, _albums())


def __getattr__(name: str) -> Callable[[], Iterator[Album]]:
    """Dynamically create functions for 'hpi query'"""
    from collections import defaultdict

    save_name = str(name)
    use_history = name.startswith("history_")

    # use history instead of to listen
    if use_history:
        name = name.lstrip("history_")

    use_all = name.startswith("all_")

    if use_all:
        name = name.lstrip("all_")

    # parse queries that look like:
    #
    # genre_rock_reason_fantano
    # genre_jazz_reason_mu
    # reason_recommended
    # reason_manual
    #
    # can have multiple genres and reasons
    # which are ANDed together
    #
    # for 'city pop', can do
    # genre_city_genre_pop
    #
    # i.e. this can be with hpi query like:
    #
    # hpi query nextalbums.genre_rock_reason_fantano
    filters = set(["genre_", "reason_"])
    filter_data = defaultdict(list)
    while any((name.startswith(f) for f in filters)):
        parts = name.split("_")
        filter_data[parts[0]].append(parts[1])
        name = "_".join(parts[2:])

    if not filter_data:
        raise AttributeError(
            f"Could not create query from or no attribute : {save_name}"
        )

    def _query() -> Iterator[Album]:
        itr = _albums() if use_all else history() if use_history else to_listen()

        for genre_filter in filter_data.get("genre", []):
            itr = filter(
                lambda a: any((genre_filter in g.lower() for g in a.genres + a.styles)),
                itr,
            )

        for reason_filter in filter_data.get("reason", []):
            itr = filter(
                lambda a: any((reason_filter in r.lower() for r in a.reasons)),
                itr,
            )

        yield from itr

    return _query


def stats() -> Stats:
    from my.core import stat

    return {
        **stat(history),
        **stat(to_listen),
    }
