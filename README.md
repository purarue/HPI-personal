These are personal modules and some of my personal scripts/jobs to save/backup data

- `my.old_forums`, parses random forum posts and achievements from sites I used to use in the past, see [`old_forums`](https://github.com/purarue/old_forums)
- `my.nextalbums`, grabbing when I listened to music albums/my ratings using my [giant spreadsheet](https://sean.fish/s/albums). Handled by [`nextalbums export`](https://github.com/purarue/albums)
- `my.location.where_db` acts as a sort of entrypoint to consume my location data -- lets me query where I was on a day, reverse geocode (using [Nominatim](https://nominatim.openstreetmap.org/ui/about.html)) lookup/query around a particular time

The most important parts of this are the `all.py` files, which override the default `all.py` in `HPI` to use my data sources:

- [`my.location.all`](./my/location/all.py) - my location data
- [`my.ip.all`](./my/ip/all.py) - my ip data

For more info on those, see [docs](https://github.com/karlicoss/HPI/blob/master/doc/MODULE_DESIGN.org#allpy)

Among the other custom scripts in [`scripts`](./scripts), includes:

- `discord-download-attachments` - to download all of my discord attachments
- `last-gps-location`, which quickly grabs my latest `gpslogger` gps location
- a custom `fzf` `Ctrl+R` for my shell which searches all of `my.zsh.history`, see [related files](https://github.com/purarue/HPI-personal/commit/4bba567a03e7c8610e7ed17a9fb4ce8db0a2faad)

## Installation

Requires `python3.10+`

To install, first follow the instructions [on my HPI repo](https://github.com/purarue/HPI#install)

Then install this as editable:

```bash
# install my HPI
git clone https://github.com/purarue/HPI-personal ./HPI-purarue-personal
python3 -m pip install -e ./HPI-purarue-personal
```

### Jobs

[`jobs`](./jobs) contains anacron-like jobs that are run periodically, using [`bgproc`](https://github.com/purarue/bgproc) and [`evry`](https://github.com/purarue/evry). In other words, those are the scripts that back up my data.

I run the jobs in the background using [supervisor](https://github.com/Supervisor/supervisor), see [here](https://github.com/purarue/dotfiles/tree/master/.local/scripts/supervisor) for my configuration, and/or [`run_jobs`](https://github.com/purarue/dotfiles/blob/master/.local/scripts/supervisor/run_jobs) for the `bgproc` wrapper. They likely won't work out of the box for you, as they depend on tokens/environment variables that are set on my system - In particular the `HPIDATA` environment variable, which for me is `~/data` -- they're here as examples if you're having issues setting up cron/scripts to backup the data
