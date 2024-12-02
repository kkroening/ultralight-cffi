from __future__ import annotations

from .. import _ffi
from .. import _stubs
from . import _base_error
from collections.abc import Generator
from contextlib import contextmanager


class UltralightJSError(_base_error.UltralightError):
    pass


@contextmanager
def scoped(
    ctx: _js_ctx.JSContext,
) -> Generator[_ffi.Pointer[_stubs.JSValueRef], None, None]:
    error_jval_refs = _ffi.new('JSValueRef *')
    yield error_jval_refs
    error_jval_ref = error_jval_refs[0]  # pylint: disable=unsubscriptable-object
    if error_jval_ref:
        error_str = _js_val.JSValue(
            error_jval_ref, ctx
        ).to_json_str()  # potentially recursive
        if error_str != '{}':
            # TODO: should probably include the JSValueRef, but need to be careful about
            # garbage collection.
            raise UltralightJSError(error_str)


from . import _js_ctx  # pylint: disable=cyclic-import,wrong-import-position
from . import _js_val  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'scoped',
    'UltralightJSError',
]
