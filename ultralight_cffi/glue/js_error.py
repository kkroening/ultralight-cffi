from .. import _ffi
from .. import _stubs
from . import _base_error
from collections.abc import Generator
from contextlib import contextmanager


class UltralightJSError(_base_error.UltralightError):
    pass


@contextmanager
def scoped(
    ctx: _stubs.JSContextRef,
) -> Generator[_ffi.Pointer[_stubs.JSValueRef], None, None]:
    error_jval_ref = _ffi.new('JSValueRef *')
    yield error_jval_ref
    error_jval = error_jval_ref[0]  # pylint: disable=unsubscriptable-object
    if error_jval:
        error_str = js_val.to_json_str(ctx, error_jval)  # potentially recursive
        if error_str != '{}':
            # TODO: should probably include the JSValueRef, but need to be careful about
            # garbage collection.
            raise UltralightJSError(error_str)


from . import js_val  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'scoped',
    'UltralightJSError',
]
