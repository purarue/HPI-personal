"""
Merges location data from multiple sources -- this includes apple location data as well
"""

from typing import Iterator

from my.core import Stats, LazyLogger

from my.location import apple  # additional source
from my.location import google_takeout, gpslogger, google_takeout_semantic
from my.util.iter import warn_exceptions

from my.location.common import Location


logger = LazyLogger(__name__, level="warning")


def locations() -> Iterator[Location]:
    yield from warn_exceptions(google_takeout_semantic.locations())
    yield from google_takeout.locations()
    yield from gpslogger.locations()
    yield from apple.locations()


def stats() -> Stats:
    from my.core import stat

    return {
        **stat(locations),
    }
