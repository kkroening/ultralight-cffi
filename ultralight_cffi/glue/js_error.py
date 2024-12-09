from __future__ import annotations

import textwrap
from .. import _ffi
from .. import _stubs
from . import _base_error
from collections.abc import Generator
from contextlib import contextmanager


class UltralightJSError(_base_error.UltralightError):
    pass


def _format_error_trace(
    error_val: _js_val.JSValue,
) -> str:
    """Formats a JavaScript error trace chain - including nested errors that potentially
    cross back and forth between Python and JavaScript.

    The output format is similar to that of Python tracebacks - particularly in terms
    of chains of exceptions.  In Python, an exception chain is formed by having a
    ``__cause__`` attribute on the exception object, and similarly in JavaScript it's
    ``cause``.  JavaScript's ``cause`` structure is not very well standardized, but the
    assumption is that the error structure is recursively self-similar - i.e. the
    ``cause`` is another error-like object, potentially having ``message``, ``stack``,
    ``traceback``, and/or another ``cause``.

    Todo:
        Maybe use :func:`JSValueIsInstanceOfConstructor` to check for ``Error`` type
        more reliably, and/or add error-friendly serialization method in
        :class:`JSValue`, as compared to :meth:`JSValue.to_json_str` or
        :meth:`JSValue.to_python` which only discover enumerable properties (and JS
        ``Error`` fields are apparently non-enumerable).
    """

    if not error_val.is_obj():
        result = ''
    else:
        error_obj = error_val.to_obj()
        lines = []

        cause_val = error_obj.get_property('cause')
        stack_val = error_obj.get_property('stack')
        traceback_val = error_obj.get_property('traceback')

        if not cause_val.is_undefined():
            lines += [
                _format_error_trace(cause_val),
                'The above exception was the direct cause of the following exception:',
                '',
            ]

        # Include *either* a JavaScript stack trace *or* a Python traceback
        if not traceback_val.is_undefined():
            lines.append(str(traceback_val))
        else:
            # JavaScript stack traces (most recent call first) are in the opposite order
            # as Python tracebacks (most recent call last).  Python tracebacks include
            # the error message at the end of the traceback, but for JS the message
            # should come before the stack trace to match the JS order.  But avoid
            # double-logging the message in the case that there's not another cause.
            message_val = error_obj.get_property('message')
            if not message_val.is_undefined() and not cause_val.is_undefined():
                lines.append(message_val.to_str())

            if not stack_val.is_undefined():
                lines.append(
                    'JavaScript stack trace:\n' + textwrap.indent(str(stack_val), '  '),
                )

        result = '\n'.join(lines)

    return result


def _format_error(
    error_val: _js_val.JSValue,
) -> str:
    """Formats a JavaScript error value/object into a consolidated string
    representation to be used for error logging.

    TMP:
        use duck-typing for JS `Error` objects having `message`, `stack`, and
    `cause` properties; fall back to serializing the JS object as JSON.

    Todo:
        Maybe use :func:`JSValueIsInstanceOfConstructor` to check for ``Error`` type
        more reliably, and/or add error-friendly serialization method in
        :class:`JSValue`, as compared to :meth:`JSValue.to_json_str` or
        :meth:`JSValue.to_python` which only discover enumerable properties (and JS
        ``Error`` fields are apparently non-enumerable).
    """

    if error_val.is_obj():
        error_obj = error_val.to_obj()
        message_val = error_obj.get_property('message')
        result = str(message_val)
        if trace_str := _format_error_trace(error_obj):
            result += '\n' + trace_str
    else:
        result = str(error_val)  # .to_json_str('')

    return result


@contextmanager
def scoped(
    ctx: _js_ctx.JSContext,
) -> Generator[_ffi.Pointer[_stubs.JSValueRef], None, None]:
    error_jval_refs = _ffi.new('JSValueRef *')
    yield error_jval_refs
    error_jval_ref = error_jval_refs[0]  # pylint: disable=unsubscriptable-object
    if error_jval_ref:
        error_val = _js_val.JSValue(error_jval_ref, ctx)
        message = _format_error(error_val)

        # TODO: should probably include the JSValueRef, but need to be careful about
        # garbage collection.

        raise UltralightJSError(message)


from . import _js_ctx  # pylint: disable=cyclic-import,wrong-import-position
from . import _js_val  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'scoped',
    'UltralightJSError',
]
