from .. import _ffi
from .. import _stubs
from . import _base_error
from collections.abc import Generator
from contextlib import contextmanager


class UltralightJSError(_base_error.UltralightError):
    pass


@contextmanager
def scoped() -> Generator[_ffi.Pointer[_stubs.JSValueRef], None, None]:
    error_jval_ref = _ffi.new('JSValueRef *')
    yield error_jval_ref
    error_jval = error_jval_ref[0]  # pylint: disable=unsubscriptable-object
    if error_jval:
        error_str = error_jval.to_json_str()  # potentially recursive
        if error_str != '{}':
            # TODO: should probably include the JSValueRef, but need to be careful about
            # garbage collection.
            raise UltralightJSError(error_str)


__all__ = [
    'scoped',
    'UltralightJSError',
]
