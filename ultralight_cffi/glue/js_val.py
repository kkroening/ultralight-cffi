import math
from .. import _ffi
from .. import _stubs
from . import js_error
from . import js_str
from collections.abc import Generator
from contextlib import contextmanager
from typing import TypeAlias
from typing import overload

PyValue: TypeAlias = str | int | float | bool | None
"""A type alias for primitive Python types that are easily convertable to respective
JavaScript values.
"""


@overload
def to_json_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    undefined_str: str,
    indent: int = 0,
) -> str: ...


@overload
def to_json_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    undefined_str: None = None,
    indent: int = 0,
) -> str | None: ...


def to_json_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    undefined_str: str | None = None,
    indent: int = 0,
) -> str | None:
    """Converts a JavaScript value into a Python JSON string representation.

    Note:
        The behavior around how to handle undefined values has subtle considerations.
        In JavaScript, the behavior of ``JSON.stringify(undefined)`` is to return
        ``undefined`` rather than a stringified `"null"` or `"undefined"`.  The default
        behavior in :func:`to_json_str` mirrors that of ``JSON.stringify``: undefined
        JS values are returned as None.

        But this is in contrast to the behavior of Python's :func:`json.dumps`, which
        returns ``"null"`` for ``json.dumps(None)``.  Such behavior can be achieved in
        :func:`to_json_str` by passing ``undefined_str='null'`.

        Alternatively, you might wish to pass ``undefined_str='undefined'`` so that
        undefined values are serialized as ``"undefined"``, which can be useful when
        :func:`to_json_str` is used for inspection, debugging, error messages, etc. -
        but note that doing so makes the output non-JSON-compliant.
    """
    with js_error.scoped(ctx) as error_jval_ref:  # potentially recursive
        jstr = _stubs.JSValueCreateJSONString(
            ctx,
            jval,
            indent,
            error_jval_ref,
        )
    if jstr == _ffi.NULL:
        pyval = undefined_str
    else:
        try:
            pyval = js_str.decode(jstr)
        finally:
            _stubs.JSStringRelease(jstr)
    return pyval


def to_none(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
) -> None:
    """Converts a JavaScript null or undefined value into a Python ``None`` value.

    This function ensures that the JS value is either null or undefined, or else raises
    :class:`TypeError`.
    """
    if not _stubs.JSValueIsNull(ctx, jval) and not _stubs.JSValueIsUndefined(ctx, jval):
        raise TypeError(
            'Expected JavaScript value to be null or undefined: '
            f'{to_json_str(ctx, jval, "undefined")}'
        )


def from_none(
    ctx: _stubs.JSContextRef,
    *,
    undefined: bool = False,
) -> _stubs.JSValueRef:
    """Creates a JavaScript null or undefined value representing a Python ``None``.

    Warning:
        The caller is responsible for protecting against garbage collection.
    """
    return (
        _stubs.JSValueMakeUndefined(ctx) if undefined else _stubs.JSValueMakeNull(ctx)
    )


def to_bool(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    *,
    strict: bool = True,
) -> bool:
    """Converts/coerces a JavaScript value into a Python :class:`bool`.

    If ``strict=True``, then the JavaScript value must specifically be a boolean value,
    or else :class:`TypeError` is raised.  Otherwise, the JS value is coerced to a
    boolean according to its truthiness.

    Todo:
        How does ``strict=True`` behave with a JS ``new Boolean()`` object, in contrast
        to a boolean literal?  These are semantically equivalent at a JS programming
        language level, but they're different kinds of values at the runtime level.
        Maybe ``strict=True`` should just not be a thing.
    """
    if not strict and _stubs.JSValueIsUndefined(ctx, jval):
        # JSValueToBoolean crashes with undefined values for some reason, despite
        # coercing other types based on truthiness.
        pyval = False
    elif strict and not _stubs.JSValueIsBoolean(ctx, jval):
        raise TypeError(
            'Expected JavaScript value to be a boolean: '
            f'{to_json_str(ctx, jval, "undefined")}'
        )
    else:
        pyval = _stubs.JSValueToBoolean(ctx, jval)
    return pyval


def from_bool(
    ctx: _stubs.JSContextRef,
    value: bool,
) -> _stubs.JSValueRef:
    """Creates a JavaScript boolean value from a Python :class:`bool`.

    Warning:
        The caller is responsible for protecting against garbage collection.
    """
    return _stubs.JSValueMakeBoolean(ctx, value)


def to_float(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    *,
    strict: bool = True,
) -> float:
    """Converts a JavaScript number value into a Python :class:`float`."""
    if strict and not _stubs.JSValueIsNumber(ctx, jval):
        raise TypeError(
            'Expected JavaScript value to be a number: '
            f'{to_json_str(ctx, jval, "undefined")}'
        )
    with js_error.scoped(ctx) as error_jval_ref:
        pyval = _stubs.JSValueToNumber(ctx, jval, error_jval_ref)
    return pyval


def from_float(
    ctx: _stubs.JSContextRef,
    value: float,
) -> _stubs.JSValueRef:
    """Creates a JavaScript number value from a Python :class:`float`.

    Warning:
        The caller is responsible for protecting against garbage collection.
    """
    return _stubs.JSValueMakeNumber(ctx, value)


def to_int(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    *,
    strict: bool = True,
) -> int:
    """Converts a JavaScript number value into a Python :class:`int`.

    Note:
        Because JavaScript has only a "number" type to be used for both integer and
        fractional (floating point) values, the conversion to Python consists of
        truncating the fractional portion (if any), of the JS number.
    """
    float_pyval = to_float(ctx, jval, strict=strict)
    if math.isnan(float_pyval):
        raise ValueError(
            f'Cannot convert NaN to int: {to_json_str(ctx, jval, "undefined")}'
        )
    if not math.isfinite(float_pyval):
        raise ValueError(
            'Cannot convert infinite number to int: '
            f'{to_json_str(ctx, jval, "undefined")}'
        )
    return int(float_pyval)


def from_int(
    ctx: _stubs.JSContextRef,
    value: int,
) -> _stubs.JSValueRef:
    """Creates a JavaScript number value from a Python :class:`int`.

    Warning:
        The caller is responsible for protecting against garbage collection.
    """
    return _stubs.JSValueMakeNumber(ctx, float(value))


def to_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    *,
    strict: bool = True,
) -> str:
    """Converts a JavaScript string value into a Python :class:`str`."""

    if strict and not _stubs.JSValueIsString(ctx, jval):
        raise TypeError(
            'Expected JavaScript value to be a string: '
            f'{to_json_str(ctx, jval, "undefined")}'
        )

    with js_error.scoped(ctx) as error_jval_ref:
        jstr = _stubs.JSValueToStringCopy(ctx, jval, error_jval_ref)
    try:
        pyval = js_str.decode(jstr)
    finally:
        if jstr != _ffi.NULL:
            _stubs.JSStringRelease(jstr)
    return pyval


def from_str(
    ctx: _stubs.JSContextRef,
    pystr: str,
) -> _stubs.JSValueRef:
    """Creates a JavaScript value from a Python string.

    Warning:
        The caller is responsible for protecting against garbage collection.
    """
    with js_str.scoped(pystr) as jstr:
        jval = _stubs.JSValueMakeString(ctx, jstr)
    return jval


def to_python(
    ctx: _stubs.JSContextRef,
    jsval: _stubs.JSValueRef,
    *,
    prefer_float: bool = False,
) -> PyValue:
    jtype = _stubs.JSValueGetType(ctx, jsval)
    pyval: PyValue
    match jtype:
        case _stubs.kJSTypeUndefined | _stubs.kJSTypeNull:
            to_none(ctx, jsval)
            pyval = None
        case _stubs.kJSTypeString:
            pyval = to_str(ctx, jsval)
        case _stubs.kJSTypeNumber:
            pyval = to_float(ctx, jsval) if prefer_float else to_int(ctx, jsval)
        case _stubs.kJSTypeBoolean:
            pyval = to_bool(ctx, jsval)
        # case _stubs.kJSTypeObject:  # TODO
        #     pyval = to_obj(ctx, jsval)
        case _:
            raise NotImplementedError(f'Unsupported JavaScript type: {jtype}')
    return pyval


def from_python(
    ctx: _stubs.JSContextRef,
    pyval: PyValue,
    *,
    prefer_undefined: bool = False,
) -> _stubs.JSValueRef:
    """Converts a Python value into a corresponding JavaScript value."""
    if pyval is None:
        jval = from_none(ctx, undefined=prefer_undefined)
    elif isinstance(pyval, bool):
        jval = from_bool(ctx, pyval)
    elif isinstance(pyval, float):
        jval = from_float(ctx, pyval)
    elif isinstance(pyval, int):
        jval = from_int(ctx, pyval)
    elif isinstance(pyval, str):
        jval = from_str(ctx, pyval)
    else:
        raise NotImplementedError(
            f'Unable to convert Python object into JavaScript: {pyval}'
        )
    return jval


@contextmanager
def scoped(
    ctx: _stubs.JSContextRef,
    val: _stubs.JSValueRef | PyValue,
) -> Generator[_stubs.JSValueRef, None, None]:
    """Context manager that wraps a value as a temporarily protected JavaScript value
    reference, automatically unprotecting the JS value when the context exits.

    If the value is not already a JS value, then it's wrapped automatically.
    """

    jval = from_python(ctx, val) if isinstance(val, PyValue) else val
    _stubs.JSValueProtect(ctx, jval)
    try:
        yield jval
    finally:
        _stubs.JSValueUnprotect(ctx, jval)


__all__ = [
    'from_bool',
    'from_float',
    'from_int',
    'from_none',
    'from_python',
    'from_str',
    'scoped',
    'to_bool',
    'to_float',
    'to_int',
    'to_json_str',
    'to_none',
    'to_python',
    'to_str',
]
