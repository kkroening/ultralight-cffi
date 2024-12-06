from __future__ import annotations

import textwrap
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

        error_val = _js_val.JSValue(error_jval_ref, ctx)
        error_dict = error_val.to_json_str()  # potentially recursive
        if isinstance(
            (error_obj := error_val.to_python(max_depth=0)), _js_obj.JSObject
        ):
            # TMP: use duck-typing for JS `Error` objects having `message` and `stack`
            # properties; fall back to serializing the JS object as JSON.
            #
            # TODO: maybe use `JSValueIsInstanceOfConstructor` to check for `Error` type
            # more reliably, and/or add error-friendly serialization method in
            # `JSValue`, as compared to `JSValue.to_json_str()` or `JSValue.to_python()`
            # which only discover enumerable properties (and JS `Error` fields are non-
            # enumerable).
            #
            # TODO: alternatively, let the JSPyObjectMapper take care of converting the
            # JS `Error` object into a respective Python error/exception object; then
            # we no longer rely on fields being enumerable or hardcoding a rule to duck-
            # type JS `Error`, and instead go through a common object mapper pathway.

            stack = error_obj.get_property('stack').to_python(max_depth=0)
            stack_str = stack if isinstance(stack, str) else None
            message = error_obj.get_property('message').to_python(max_depth=0)
            message_str = message if isinstance(message, str) else None
        else:
            stack_str = None
            message_str = None

        if message_str is not None and stack_str is not None:
            message = '\n'.join(
                [
                    message_str,
                    error_dict if error_dict is not None else '',
                    'JavaScript stack trace:\n' + textwrap.indent(stack_str, '  '),
                ]
            )
        else:
            message = str(error_val)

        # TODO: should probably include the JSValueRef, but need to be careful about
        # garbage collection.
        raise UltralightJSError(message)


from . import _js_ctx  # pylint: disable=cyclic-import,wrong-import-position
from . import _js_obj  # pylint: disable=cyclic-import,wrong-import-position
from . import _js_val  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'scoped',
    'UltralightJSError',
]
