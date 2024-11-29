from .. import _ffi
from .. import _stubs
from . import _base_error
from collections.abc import Generator
from contextlib import contextmanager


class UltralightULError(_base_error.UltralightError):
    """An exception originating from Ultralight itself from the ``ul*`` API.

    For example, if :func:`_stubs.ulViewEvaluateScript` produces an exception string,
    it gets wrapped in a :class:`UltralightULError` and then raised as a proper Python
    exception.

    See also:
        :class:`_js_misc.UltralightJSError`: An exception originating from Ultralight's
        ``JS*`` API (rather than ``ul*``) with an associated JavaScript value rather
        than a string.
    """


@contextmanager
def scoped() -> Generator[_ffi.Pointer[_stubs.ULString], None, None]:
    error_ulstr_ref = _ffi.new('ULString *')
    try:
        yield error_ulstr_ref
    finally:
        error_ulstr = error_ulstr_ref[0]  # pylint: disable=unsubscriptable-object
        error_str = _stubs.ulStringGetData(error_ulstr)
        if error_str:
            raise UltralightULError(error_str)


__all__ = [
    'scoped',
    'UltralightULError',
]
