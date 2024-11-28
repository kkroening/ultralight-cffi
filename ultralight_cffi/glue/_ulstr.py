from .. import _stubs
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def ulstr_scope(
    pystr: str,
) -> Generator[_stubs.ULString, None, None]:
    ulstr = _stubs.ulCreateStringUTF8(pystr.encode(), len(pystr.encode()))
    try:
        yield ulstr
    finally:
        _stubs.ulDestroyString(ulstr)
