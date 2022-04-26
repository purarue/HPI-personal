"""
Merges location data from multiple sources -- this includes apple location data as well
"""

from typing import Iterator

from my.core import Stats, LazyLogger

from my.location import via_ip, google_takeout, gpslogger
from my.location import apple  # additional source

from my.location.common import Location


logger = LazyLogger(__name__, level="warning")


def locations() -> Iterator[Location]:
    yield from google_takeout.locations()
    yield from via_ip.locations()
    yield from gpslogger.locations()
    yield from apple.locations()


def stats() -> Stats:
    from my.core import stat

    return {
        **stat(locations),
    }
