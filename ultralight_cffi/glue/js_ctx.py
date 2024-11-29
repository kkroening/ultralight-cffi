from .. import _ffi
from .. import _stubs
from . import js_str
from collections.abc import Generator
from contextlib import contextmanager


def get_name(
    ctx: _stubs.JSGlobalContextRef,
) -> str:
    """Gets the name of a global JavaScript context."""
    name_jstr = _stubs.JSGlobalContextCopyName(ctx)
    try:
        name_pystr = js_str.decode(name_jstr)
    finally:
        _stubs.JSStringRelease(name_jstr)
    return name_pystr


def set_name(
    ctx: _stubs.JSGlobalContextRef,
    name: str,
) -> None:
    """Sets the name of a global JavaScript context."""
    with js_str.scoped(name) as name_jstr:
        _stubs.JSGlobalContextSetName(ctx, name_jstr)


@contextmanager
def scoped_global(
    ctx: _stubs.JSGlobalContextRef | None = None,
) -> Generator[_stubs.JSGlobalContextRef, None, None]:
    """Context manager that creates/retains and automatically releases a global
    JavaScript context.

    If no ``ctx`` is provided, a new context is created; but regardless, the context
    (new or existing) is retained for the life of the context manager and then released
    when the context exits.
    """
    if ctx is None:
        ctx = _stubs.JSGlobalContextCreate(_ffi.NULL)
    else:
        ctx = _stubs.JSGlobalContextRetain(ctx)
    try:
        yield ctx
    finally:
        _stubs.JSGlobalContextRelease(ctx)


__all__ = [
    'scoped_global',
]
