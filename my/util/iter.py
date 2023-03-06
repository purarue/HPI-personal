"""
Error-aware iterator transformers

These drop/warn/raise exceptions from an iterator which may contain errors
to produce a new iterator which does not contain errors, useful when
combining iterators in all.py files
"""

from typing import TypeVar, Iterator

from my.core.common import LazyLogger
from my.core.error import Res

logger = LazyLogger(__name__)

T = TypeVar("T")


def drop_exceptions(it: Iterator[Res[T]]) -> Iterator[T]:
    for x in it:
        if not isinstance(x, Exception):
            yield x


def warn_exceptions(it: Iterator[Res[T]]) -> Iterator[T]:
    for x in it:
        if isinstance(x, Exception):
            logger.error(x)
        else:
            yield x


def raise_exceptions(it: Iterator[Res[T]]) -> Iterator[T]:
    for x in it:
        if isinstance(x, Exception):
            raise x
        else:
            yield x
