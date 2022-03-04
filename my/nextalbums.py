"""
Parses albums from my google sheet
https://github.com/seanbreckenridge/albums
https://sean.fish/s/albums
"""

# see https://github.com/seanbreckenridge/dotfiles/blob/master/.config/my/my/config/__init__.py for an example
from my.config import nextalbums as user_config  # type: ignore[attr-defined]
from my.core import Paths, dataclass


@dataclass
class config(user_config):
    # path[s]/glob to the exported data. Resulting file from 'nextalbums export'
    export_path: Paths


from pathlib import Path
from typing import Iterator

from nextalbums.export import Album, read_dump
from my.core import get_files, Stats


# should only ever be one dump, the .job overwrites the file
def input() -> Path:
    dump = list(get_files(config.export_path))
    assert len(dump) == 1, "Expected one JSON file as input"
    return dump[0]


def _albums() -> Iterator[Album]:
    yield from read_dump(input())


def history() -> Iterator[Album]:
    """Only return items I've listened to, where the score is not null"""
    yield from filter(lambda a: a.listened, _albums())


def to_listen() -> Iterator[Album]:
    """Albums I have yet to listen to"""
    yield from filter(lambda a: not a.listened and not a.dropped, _albums())


def stats() -> Stats:
    from my.core import stat

    return {
        **stat(history),
        **stat(to_listen),
    }
