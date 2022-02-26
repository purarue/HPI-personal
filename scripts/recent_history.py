#!/usr/bin/env python3

"""
Copy, open and print url/metadata from
the current firefox database

Used with the recent_history script
"""

import json
from browserexport.browsers.firefox import Firefox
from browserexport.parse import read_visits
from sqlite_backup.core import sqlite_backup
from more_itertools import unique_everseen

conn = sqlite_backup(Firefox.locate_database())
assert conn is not None
for visit in unique_everseen(read_visits(conn), key=lambda v: v.url):
    print(
        json.dumps(
            {"url": visit.url, "metadata": getattr(visit.metadata, "description", "")}
        )
    )
