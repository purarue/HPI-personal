"""
Unrelated to the other sources here, uses locations to generate a data (JSON) file
which tracks where I was on each hour/day, making it fast/easy to query from my phone

This is all pretty messy, to make sense for using my data, it uses some (configurable through
the config) heuristics, falling back to my.location.home if I don't have any data, and
re-using old locations for holes in data sources

In the background I run 'hpi query my.location.where_db.gen > ~/data/where_db.json' to save to a
database once a day to update

Then 'python3 -m my.location.where_db' accepts any sort of date-like string and queries the db
printing the latitude/longitute.

TODO: could display this nicely in the terminal or something? or grab more information from location by querying some location service
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Sequence, Iterator, Optional, List, Tuple, Mapping, NamedTuple
from functools import cache
from datetime import datetime, date, timedelta

from my.core import make_config, PathIsh, dataclass
from my.location.common import Location, LatLon

from my.config import location


@dataclass
class user_config(location.where_db):  # type: ignore
    # accuracy for locations to be able to use them
    # defaults to 300m
    accuracy_filter: Optional[int] = None

    # how far we should be from the last point (metres) to create a new one
    # defaults to 100m
    new_point_distance: Optional[int] = None

    # how often we should send a new time, even if we haven't moved
    # defaults to 3h
    new_point_duration: Optional[timedelta] = None

    # after this date, rely on locations more than fallbacks
    # i.e., some date you after which you have accurate locations (I use gpslogger for this)
    # if not provided, doesnt do heuristics
    accurate_date_cutoff: Optional[date] = None

    # if we're missing accurate data after the cutoff, use the previous location
    # till we have new data for this many days
    # if not provided, doesnt do heuristics
    previous_accurate_for_days: Optional[int] = None

    # location for the database
    # required to query to where you save the database
    database_location: Optional[PathIsh] = None


config = make_config(user_config)


# just for loading/querying the database
ModelRaw = Tuple[float, float, int]


class Model(NamedTuple):
    lat: float
    lon: float
    epoch: int


class ModelDt(NamedTuple):
    lat: float
    lon: float
    dt: datetime


def _serialize(loc: Location) -> ModelDt:
    return ModelDt(loc.lat, loc.lon, loc.dt)


def generate_from_locations() -> Iterator[ModelDt]:
    import geopy.distance  # type: ignore[import]
    from my.location.all import locations as location_sources

    use_accuracy = config.accuracy_filter if config.accuracy_filter is not None else 300
    new_dist = (
        config.new_point_distance if config.new_point_distance is not None else 100
    )

    locs: List[Location] = [
        loc
        for loc in location_sources()
        if loc.accuracy is not None and loc.accuracy < use_accuracy
    ]
    locs.sort(key=lambda l: l.dt)
    last: Location = locs[0]
    yield _serialize(last)
    new_point_distance = (
        config.new_point_duration
        if config.new_point_duration is not None
        else timedelta(hours=3)
    )
    assert isinstance(new_point_distance, timedelta)

    for cur in locs[1:]:
        last_latlon: LatLon = (last.lat, last.lon)
        cur_latlon: LatLon = (cur.lat, cur.lon)
        dist = geopy.distance.distance(last_latlon, cur_latlon)
        # if we've hit distance filter threshold, or we haven't
        # sent a location recently, send a new one
        if dist.m > new_dist or cur.dt - last.dt > new_point_distance:
            yield _serialize(cur)
            last = cur


@cache
def _homes(reverse: bool = False) -> List[Tuple[datetime, LatLon]]:
    """cached home data"""
    from my.location.home import config

    hist: List[Tuple[datetime, LatLon]] = list(config._history)
    hist.sort(key=lambda data: data[0], reverse=reverse)
    return hist


def _home(on_dt: datetime) -> ModelDt:
    """
    given a datetime, give the location/date of my home at the time
    """
    ndt = _naive(on_dt)
    for dt, (lat, lon) in _homes(reverse=True):
        if ndt >= _naive(dt):
            return ModelDt(lat, lon, _naive(dt))

    # default to last home
    last = _homes()[-1]
    ldt, (llon, llat) = last
    return ModelDt(llat, llon, _naive(ldt))


def _naive(dt: datetime) -> datetime:
    """remove timezone from a datetime"""
    return datetime.fromtimestamp(dt.timestamp())


def generate() -> Iterator[ModelDt]:
    import more_itertools

    # relate each item to a day, and add that to a list
    # if none present on that day, default to my home location
    loc_on_day: Mapping[date, List[ModelDt]] = defaultdict(list)
    for loc in generate_from_locations():
        _, _, dt = loc
        loc_on_day[dt.date()].append(loc)

    # start at the first date available + 1 day to account for weird timezone stuff
    cur: datetime = _naive(_homes()[0][0]) + timedelta(days=1)

    # or, if we actually have location data that far back, use locations
    first_key = more_itertools.first(sorted(loc_on_day.keys()))
    if first_key < cur.date():
        cur = loc_on_day[first_key][0].dt
        assert isinstance(
            cur, datetime
        ), f"error extracting dt from first location {loc_on_day[first_key]}"

    # if we've had some accurate locations, use
    # those for a week instead of home
    last_accurate: Optional[ModelDt] = None

    # loop through a day at a time, either using home
    # or using the dates generated from locations
    while cur <= datetime.now():
        # if we dont have accurate up to date locations
        if cur.date() not in loc_on_day:
            # continue using last accurate timestamp/location till we have a new one
            # or its been config.previous_accurate_for_days (how long we should keep using
            # an old location if were missing data) days since the last accurate one
            if (
                config.previous_accurate_for_days is not None
                and config.accurate_date_cutoff is not None
                and last_accurate is not None
                and (
                    cur.date() >= config.accurate_date_cutoff
                    or abs((cur - _naive(last_accurate.dt)).days)
                    < config.previous_accurate_for_days
                )
            ):
                yield ModelDt(last_accurate.lat, last_accurate.lon, cur)
            else:
                # else, fallback to use home location
                last_home = _home(cur)
                yield ModelDt(last_home.lat, last_home.lon, cur)
        else:
            # we have accurate locations, use those
            for aloc in loc_on_day[cur.date()]:
                yield aloc
                # save current accurate location so we can estimate if we want
                last_accurate = aloc
        cur += timedelta(days=1)


# CLI

import click


# Run 'hpi query my.location.where_db.gen'
def gen() -> Iterator[ModelRaw]:
    for loc in generate():
        yield loc.lat, loc.lon, int(loc.dt.timestamp())


Database = List[ModelRaw]


def _db() -> Optional[Path]:
    if config.database_location is None:
        return None
    return Path(config.database_location).expanduser().absolute()


def locations(db_location: Optional[Path] = None) -> Iterator[ModelRaw]:
    from my.core.warnings import medium

    if db_location is None:
        db_location = _db()
    if db_location is None:
        medium(
            "No database found -- set one on your where_db config as 'database_location'"
        )
        return
    with open(db_location, "r") as f:
        data = json.load(f)
        assert isinstance(data, list)
    yield from iter(data)


def _parse_datetimes(dates: Sequence[str]) -> Iterator[int]:
    import dateparser

    for d in dates:
        ds = d.strip()
        if len(ds) == 0:
            click.echo("Recieved empty string input", err=True)
            return
        dt = dateparser.parse(ds)
        if dt is None:
            click.echo(f"Could not parse {d} into a date", err=True)
            continue
        else:
            yield int(dt.timestamp())


def _run_query(epoch: int, db: Database) -> Tuple[float, float]:
    for (lat, lon, ts) in db:
        if ts > epoch:
            return lat, lon
    lat, lon, _ = db[-1]
    return lat, lon


@click.command(short_help="query database")
@click.option(
    "--db",
    help="read from database",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    required=True,
    default=_db(),
)
@click.option("--url/--no-url", is_flag=True, help="print google location URL")
@click.argument("DATE", type=str, required=True, nargs=-1)
def query(db: Path, url: bool, date: Sequence[str]) -> None:
    """
    Queries the current database to figure out where I was on a particular date
    """
    dts = list(_parse_datetimes(date))
    data = list(locations(db))
    for d in dts:
        lat, lon = _run_query(d, db=data)
        if url:
            click.echo(f"https://www.google.com/search?q={lat}%2C{lon}")
        else:
            click.echo(f"{lat},{lon}")


if __name__ == "__main__":
    query()
