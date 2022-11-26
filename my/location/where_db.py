"""
Unrelated to the other sources here, uses locations to generate a data (JSON) file
which tracks where I was on each hour/day, making it fast/easy to query from my phone

This is all pretty messy, to make sense for using my data, it uses some (configurable through
the config) heuristics, falling back to my.location.home if I don't have any data, and
re-using old locations for holes in data sources

In the background I run 'hpi query my.location.where_db.gen > ~/data/where_db.json' to save to a
database once every few hours to update

Then 'python3 -m my.location.where_db query' accepts any sort of date-like string and queries the db
printing the latitude/longitude.
"""

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import (
    Iterator,
    Optional,
    List,
    Tuple,
    Mapping,
    NamedTuple,
    Iterable,
    Sequence,
)
from functools import cache
from datetime import datetime, date, timedelta

from my.core import make_config, PathIsh, dataclass
from my.core.warnings import medium
from my.location.common import Location, LatLon

from my.config import location

# see https://github.com/seanbreckenridge/dotfiles/blob/master/.config/my/my/config/__init__.py for an example of config
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
    from my.location.home import config as home_config

    hist: List[Tuple[datetime, LatLon]] = list(home_config._history)
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

    # go past one day, incase of timezone-issues
    tomorrow = datetime.now() + timedelta(days=1)

    # loop through a day at a time, either using home
    # or using the dates generated from locations
    while cur <= tomorrow:
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


def _parse_datetimes(
    ctx: click.Context, param: click.Argument, value: Sequence[str]
) -> Iterator[int]:
    import dateparser
    import warnings

    # remove pytz warning from dateparser module
    warnings.filterwarnings("ignore", "The localize method is no longer necessary")

    for d in value:
        ds = d.strip()
        if len(ds) == 0:
            raise click.BadParameter(f"Received empty string as input")
        dt = dateparser.parse(ds)
        if dt is None:
            raise click.BadParameter(f"Could not parse '{d}' into a date")
        else:
            yield int(dt.timestamp())


def _parse_timedelta(
    ctx: click.Context, param: click.Argument, value: Optional[str]
) -> Optional[timedelta]:
    if value is None:
        return None

    from my.core.query_range import parse_timedelta_string

    try:
        return parse_timedelta_string(value)
    except ValueError as v:
        raise click.BadParameter(str(v))


def _run_query(
    epoch: int,
    db: Database,
    around: Optional[timedelta] = None,
) -> Iterator[ModelRaw]:
    if epoch < db[0][2]:
        medium(
            f"Query datetime is before first location in db, returning first location"
        )
        yield db[0]
        return

    if around is None:
        for loc in db:
            if loc[2] >= epoch:
                yield loc
                return

        medium("Matched no timestamp, returning most recent location")
        yield db[-1]
    else:
        seconds = around.total_seconds()
        for loc in db:
            if abs(loc[2] - epoch) <= seconds:
                yield loc


@click.group(help=__doc__)
def main() -> None:
    pass


@main.command(short_help="query database")
@click.option(
    "--db",
    help="read from database",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    required=True,
    default=_db(),
)
@click.option(
    "-o",
    "--output",
    type=click.Choice(["plain", "google_url", "geolocate", "json"]),
    multiple=True,
    default=("plain",),
    help="how to print output (latitude/longitude)",
)
@click.option(
    "-a",
    "--around",
    type=click.UNPROCESSED,
    callback=_parse_timedelta,
    default=None,
)
@click.argument(
    "DATE", type=click.UNPROCESSED, callback=_parse_datetimes, required=True, nargs=-1
)
def query(
    db: Path, output: Sequence[str], around: Optional[timedelta], date: Iterable[int]
) -> None:
    """
    Queries the current database to figure out where I was on a particular date
    """
    dts = list(date)
    fts = datetime.fromtimestamp  # 'from timestamp'
    output_fmts = set(output)
    for d in dts:
        res = list(_run_query(d, db=list(locations(db)), around=around))
        if len(res) == 0 and around is not None:
            medium(f"No locations found {around} around timestamp {fts(d)}")
        for lat, lon, ts in res:
            if "plain" in output_fmts:
                if around:
                    click.echo(f"{fts(ts)} {lat},{lon}")
                else:
                    click.echo(f"{lat},{lon}")
            if "google_url" in output_fmts:
                click.echo(f"https://www.google.com/search?q={lat}%2C{lon}")
            if "geolocate" in output_fmts:
                import geopy.geocoders  # type: ignore[import]

                nom = geopy.geocoders.Nominatim(
                    user_agent="seanbreckenridge/HPI-personal/where_db",
                )
                info = nom.reverse((lat, lon), timeout=3)  # type: ignore
                click.echo(str(info))
                # only sleep if we're making more than one request
                if len(res) > 1 or len(dts) > 1:
                    time.sleep(1)

        if "json" in output_fmts:
            from my.core.serialize import dumps

            click.echo(dumps([ModelDt(lat, lon, fts(ts)) for lat, lon, ts in res]))


if __name__ == "__main__":
    main()
