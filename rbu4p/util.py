import contextlib
import itertools
import sys
import typing as t
import warnings

import urllib3.exceptions

if t.TYPE_CHECKING:
    from _typeshed import SupportsRichComparison


@contextlib.contextmanager
def ignore_warnings(category=Warning):
    try:
        with warnings.catch_warnings(category=category):
            warnings.simplefilter("ignore")
            yield
    finally:
        pass


@contextlib.contextmanager
def allow_insecure(insecure: t.Optional[bool]):
    if insecure:
        ctx = ignore_warnings(urllib3.exceptions.InsecureRequestWarning)
    else:
        ctx = contextlib.nullcontext()

    with ctx:
        try:
            yield
        finally:
            pass


def groupby[T](it: t.Iterable[T], key: t.Callable[[T], "SupportsRichComparison"]):
    return itertools.groupby(sorted(it, key=key), key=key)


def is_interactive() -> bool:
    return sys.__stdin__.isatty()


@t.overload
def str2bool(s: t.Any, /) -> bool: ...
@t.overload
def str2bool(s: t.Any, /, *, allow_none: t.Literal[False]) -> t.Optional[bool]: ...
@t.overload
def str2bool(s: t.Any, /, *, allow_none: t.Literal[True]) -> t.Optional[bool]: ...
def str2bool(s: t.Any, /, *, allow_none: bool = False) -> t.Optional[bool]:
    s = str(s or "").strip()
    if allow_none and not s:
        return None
    return s.lower() in {"true", "1", "yes", "on", "y"}
