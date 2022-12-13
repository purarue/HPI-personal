These are personal modules and some of my personal scripts/jobs to save/backup data

- `my.old_forums`, parses random forum posts and achievements from sites I used to use in the past, see [`old_forums`](https://github.com/seanbreckenridge/old_forums)
- `my.nextalbums`, grabbing when I listened to music albums/my ratings using my [giant spreadsheet](https://sean.fish/s/albums). Handled by [`nextalbums export`](https://github.com/seanbreckenridge/albums)
- `my.location.where_db` acts as a sort of entrypoint to consume my location data -- lets me query where I was on a day, reverse geocode (using [Nominatim](https://nominatim.openstreetmap.org/ui/about.html)) lookup/query around a particular time

Among the other custom scripts in [`scripts`](./scripts), includes:

- `discord_download_attachments` - to download all of my discord attachments
- `last_gps_location`, which quickly grabs my latest `gpslogger` gps location
- a custom `fzf` `Ctrl+R` for my shell which searches all of `my.zsh.history`, see [related files](https://github.com/seanbreckenridge/HPI-personal/commit/4bba567a03e7c8610e7ed17a9fb4ce8db0a2faad)

## Installation

Requires `python3.7+`

To install, first follow the instructions [on my HPI repo](https://github.com/seanbreckenridge/HPI#install)

Then install this as editable:

```
# install my HPI
git clone https://github.com/seanbreckenridge/HPI-personal ./HPI-seanbreckenridge-personal
python3 -m pip install -e ./HPI-seanbreckenridge-personal
```

### Jobs

[`jobs`](./jobs) contains anacron-like jobs that are run periodically, using [`bgproc`](https://github.com/seanbreckenridge/bgproc) and [`evry`](https://github.com/seanbreckenridge/evry). In other words, those are the scripts that back up my data.

I run the jobs in the background using [supervisor](https://github.com/Supervisor/supervisor), see [here](https://github.com/seanbreckenridge/dotfiles/tree/master/.local/scripts/supervisor) for my configuration, and/or [`run_jobs`](https://github.com/seanbreckenridge/dotfiles/blob/master/.local/scripts/supervisor/run_jobs) for the `bgproc` wrapper. They likely won't work out of the box for you, as they depend on tokens/environment variables that are set on my system - In particular the `HPIDATA` environment variable, which for me is `~/data` -- they're here as examples if you're having issues setting up cron/scripts to backup the data
