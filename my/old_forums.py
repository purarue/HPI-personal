"""
Manually Scraped Forum Posts from Random Forums I've used in the past
https://github.com/purarue/forum_parser
"""

REQUIRES = ["git+https://github.com/purarue/old_forums"]

from dataclasses import dataclass

# see https://github.com/purarue/dotfiles/blob/master/.config/my/my/config/__init__.py for an example
from my.config import old_forums as user_config  # type: ignore[attr-defined]

from my.core import Paths


@dataclass
class config(user_config):
    # path[s]/glob to the folder which contains JSON/HTML files
    export_path: Paths


import os
from pathlib import Path
from collections.abc import Sequence, Iterator

from autotui.shortcuts import load_from
from old_forums.forum import Post  # model from lib
from old_forums.achievements import AchievementSelector, Achievement

from my.core import get_files, Stats, make_logger

logger = make_logger(__name__, level="warning")


def forum_posts_inputs() -> Sequence[Path]:
    return get_files(config.export_path, glob="*.json")


def achievement_inputs() -> Sequence[Path]:
    return get_files(config.export_path, glob="*.html")


def forum_posts() -> Iterator[Post]:
    for path in forum_posts_inputs():
        yield from load_from(Post, path)


def achievements() -> Iterator[Achievement]:
    # quite personal, lets me specify CSS selectors as a JSON config file, see:
    # https://github.com/purarue/old_forums
    sels = AchievementSelector.load_from_blob(open(os.environ["OLD_FORUMS_SELECTORS"]))
    for path in achievement_inputs():
        with path.open("r") as f:
            try:
                yield from Achievement.parse_using_selectors(f, sels)
            except RuntimeError as e:
                logger.warning(f"error parsing {path}: {e}")


def stats() -> Stats:
    from my.core import stat

    return {**stat(forum_posts), **stat(achievements)}
