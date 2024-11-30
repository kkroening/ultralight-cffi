from __future__ import annotations

import math
from .. import _ffi
from .. import _stubs
from . import js_error
from . import js_str
from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import Self
from typing import TypeAlias
from typing import cast
from typing import overload

PyPrimitive: TypeAlias = str | int | float | bool | None
"""A type alias for primitive Python types that are easily convertable to respective
JavaScript values.
"""


PyDictAny: TypeAlias = Mapping
PyListAny: TypeAlias = Sequence

if TYPE_CHECKING:
    # Self-referential types are fine during type-checking, but problematic at runtime
    PyDict: TypeAlias = PyDictAny[str, 'PyValue']
    PyList: TypeAlias = PyListAny['PyValue']
    PyValue: TypeAlias = 'JSValue' | PyPrimitive | PyList | PyDict
else:
    PyDict = PyDictAny
    PyList = PyListAny
    PyValue: TypeAlias = Any


@dataclass(frozen=True)
class JSValue:
    ref: _stubs.JSValueRef
    ctx: _stubs.JSContextRef

    @overload
    def to_json_str(
        self,
        undefined_str: str,
        indent: int = 0,
    ) -> str: ...

    @overload
    def to_json_str(
        self,
        undefined_str: None = None,
        indent: int = 0,
    ) -> str | None: ...

    def to_json_str(
        self,
        undefined_str: str | None = None,
        indent: int = 0,
    ) -> str | None:
        """Converts a JavaScript value into a Python JSON string representation.

        Note:
            The behavior around how to handle undefined values has subtle
            considerations.  In JavaScript, the behavior of
            ``JSON.stringify(undefined)`` is to return ``undefined`` rather than a
            stringified `"null"` or `"undefined"`.  The default behavior in
            :func:`to_json_str` mirrors that of ``JSON.stringify``: undefined JS values
            are returned as None.

            But this is in contrast to the behavior of Python's :func:`json.dumps`,
            which returns ``"null"`` for ``json.dumps(None)``.  Such behavior can be
            achieved in :func:`to_json_str` by passing ``undefined_str='null'`.

            Alternatively, you might wish to pass ``undefined_str='undefined'`` so that
            undefined values are serialized as ``"undefined"``, which can be useful when
            :func:`to_json_str` is used for inspection, debugging, error messages, etc.
            - but note that doing so makes the output non-JSON-compliant.
        """
        with js_error.scoped(self.ctx) as error_jval_ptr:  # potentially recursive
            jstr = _stubs.JSValueCreateJSONString(
                self.ctx,
                self.ref,
                indent,
                error_jval_ptr,
            )
        if jstr == _ffi.NULL:
            pyval = undefined_str
        else:
            try:
                pyval = js_str.decode(jstr)
            finally:
                _stubs.JSStringRelease(jstr)
        return pyval

    def to_none(self) -> None:
        """Converts a JavaScript null or undefined value into a Python ``None`` value.

        This function ensures that the JS value is either null or undefined, or else
        raises :class:`TypeError`.
        """
        if not _stubs.JSValueIsNull(
            self.ctx, self.ref
        ) and not _stubs.JSValueIsUndefined(self.ctx, self.ref):
            raise TypeError(
                'Expected JavaScript value to be null or undefined: '
                f'{self.to_json_str("undefined")}'
            )

    @classmethod
    def from_none(
        cls,
        ctx: _stubs.JSContextRef,
        *,
        undefined: bool = False,
    ) -> Self:
        """Creates a JavaScript null or undefined value representing a Python ``None``.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = (
            _stubs.JSValueMakeUndefined(ctx)
            if undefined
            else _stubs.JSValueMakeNull(ctx)
        )
        return cls(ref, ctx)

    def to_bool(
        self,
        *,
        strict: bool = True,
    ) -> bool:
        """Converts/coerces a JavaScript value into a Python :class:`bool`.

        If ``strict=True``, then the JavaScript value must specifically be a boolean
        value, or else :class:`TypeError` is raised.  Otherwise, the JS value is coerced
        to a boolean according to its truthiness.

        Todo:
            How does ``strict=True`` behave with a JS ``new Boolean()`` *object*, in
            contrast to a boolean literal?  These are semantically equivalent at a JS
            programming language level, but they're different kinds of values at the
            runtime level.  Maybe ``strict=True`` should just not be a thing.
        """
        if not strict and _stubs.JSValueIsUndefined(self.ctx, self.ref):
            # JSValueToBoolean crashes with undefined values for some reason, despite
            # coercing other types based on truthiness.
            pyval = False
        elif strict and not _stubs.JSValueIsBoolean(self.ctx, self.ref):
            raise TypeError(
                'Expected JavaScript value to be a boolean: '
                + self.to_json_str('undefined')
            )
        else:
            pyval = _stubs.JSValueToBoolean(self.ctx, self.ref)
        return pyval

    @classmethod
    def from_bool(
        cls,
        ctx: _stubs.JSContextRef,
        value: bool,
    ) -> Self:
        """Creates a JavaScript boolean value from a Python :class:`bool`.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = _stubs.JSValueMakeBoolean(ctx, value)
        return cls(ref, ctx)

    def to_float(
        self,
        *,
        strict: bool = True,
    ) -> float:
        """Converts a JavaScript number value into a Python :class:`float`."""
        if strict and not _stubs.JSValueIsNumber(self.ctx, self.ref):
            raise TypeError(
                'Expected JavaScript value to be a number: '
                + self.to_json_str('undefined')
            )
        with js_error.scoped(self.ctx) as error_jval_ptr:
            pyval = _stubs.JSValueToNumber(self.ctx, self.ref, error_jval_ptr)
        return pyval

    @classmethod
    def from_float(
        cls,
        ctx: _stubs.JSContextRef,
        value: float,
    ) -> Self:
        """Creates a JavaScript number value from a Python :class:`float`.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = _stubs.JSValueMakeNumber(ctx, value)
        return cls(ref, ctx)

    def to_int(
        self,
        *,
        strict: bool = True,
    ) -> int:
        """Converts a JavaScript number value into a Python :class:`int`.

        Note:
            Because JavaScript has only a "number" type to be used for both integer and
            fractional (floating point) values, the conversion to Python consists of
            truncating the fractional portion (if any), of the JS number.
        """
        float_pyval = self.to_float(strict=strict)
        if math.isnan(float_pyval):
            raise ValueError(
                'Cannot convert NaN to int: ' + self.to_json_str('undefined')
            )
        if not math.isfinite(float_pyval):
            raise ValueError(
                'Cannot convert infinite number to int: '
                + self.to_json_str('undefined')
            )
        return int(float_pyval)

    @classmethod
    def from_int(
        cls,
        ctx: _stubs.JSContextRef,
        value: int,
    ) -> Self:
        """Creates a JavaScript number value from a Python :class:`int`.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = _stubs.JSValueMakeNumber(ctx, float(value))
        return cls(ref, ctx)

    def to_str(
        self,
        *,
        strict: bool = True,
    ) -> str:
        """Converts a JavaScript string value into a Python :class:`str`."""

        if strict and not _stubs.JSValueIsString(self.ctx, self.ref):
            raise TypeError(
                'Expected JavaScript value to be a string: '
                + self.to_json_str('undefined')
            )

        with js_error.scoped(self.ctx) as error_jval_ptr:
            jstr = _stubs.JSValueToStringCopy(self.ctx, self.ref, error_jval_ptr)
        try:
            pyval = js_str.decode(jstr)
        finally:
            if jstr != _ffi.NULL:
                _stubs.JSStringRelease(jstr)
        return pyval

    @classmethod
    def from_str(
        cls,
        ctx: _stubs.JSContextRef,
        pystr: str,
    ) -> Self:
        """Creates a JavaScript value from a Python string.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        with js_str.scoped(pystr) as jstr:
            ref = _stubs.JSValueMakeString(ctx, jstr)
        return cls(ref, ctx)

    def to_dict(
        self,
        *,
        max_depth: int = 5,  # TODO: make optional
        prefer_float: bool = False,
        strict: bool = True,
    ) -> PyDict:
        """Converts a JavaScript object value into a Python dictionary (recursively, up
        to some depth limit).

        The depth is limited to prevent infinite recursion in the case of cyclic object
        references.

        Todo:
            Ideally be more intelligent about cyclic references without relying on a
            depth limit - e.g. by making a mapping of seen objects.
        """

        if not _stubs.JSValueIsObject(self.ctx, self.ref):
            raise TypeError(
                'Expected JavaScript value to be an object: '
                + self.to_json_str('undefined')
            )
        if strict and _stubs.JSValueIsArray(self.ctx, self.ref):
            # Array objects can technically be converted to a Python dict, but it's
            # likely not intentional, unless explicitly requested via `strict=False`.
            raise TypeError(
                'Expected JavaScript value to be a non-array object: '
                + self.to_json_str('undefined')
            )

        shallow_dict = js_obj.to_shallow_dict(self.ctx, self.ref)
        return (
            {
                k: JSValue(v, self.ctx).to_python(
                    max_depth=max_depth - 1,
                    prefer_float=prefer_float,
                )
                for k, v in shallow_dict.items()
            }
            if max_depth
            else cast(PyDict, shallow_dict)
        )

    @classmethod
    def from_dict(
        cls,
        ctx: _stubs.JSContextRef,
        pydict: PyDict,
        # jcls: _stubs.JSClassRef | None = None,
        *,
        prefer_undefined: bool = False,
    ) -> Self:
        jobj_ref = _stubs.JSObjectMake(ctx, _ffi.NULL, _ffi.NULL)
        for key, pyval in pydict.items():
            with cls.scoped_from(ctx, pyval, prefer_undefined=prefer_undefined) as jval:
                js_obj.set_property(ctx, jobj_ref, key, jval.ref)
        return cls(jobj_ref, ctx)

    def to_list(
        self,
        *,
        prefer_float: bool = False,
        max_depth: int = 5,  # TODO: make optional
    ) -> PyList:
        """Converts a JavaScript object value into a Python list (recursively)."""
        if not _stubs.JSValueIsArray(self.ctx, self.ref):
            raise TypeError(
                'Expected JavaScript value to be an array object: '
                + self.to_json_str('undefined')
            )

        # length_jval_ref = js_obj.get_property(self.ctx, self.ref, 'length')
        # length = JSValue(length_jval_ref, self.ctx).to_int()

        pylist: list[PyValue] = []
        for index_str, jval_ref in js_obj.to_shallow_dict(self.ctx, self.ref).items():
            # Note: Technically, JS arrays can contain elements with bizarre keys, such
            # as weird unicode characters (including aliases of number characters),
            # discontiguous index ranges, negative numbers, etc. - but for simplicity
            # all such oddities are ignored, and the items are converted according to
            # their property order taken at face value.  Fortunately, multi-digit
            # numbers do sort correctly - i.e. "10" being greater than "2" - rather than
            # alphabetically, so trusting the order, discarding any weird keys, and
            # ignoring discontinuities is reasonably correct in 99.999% of the time, and
            # the remainder of cases are just asking for trouble anyways.

            if index_str.isascii() and index_str.isnumeric():
                jval = JSValue(jval_ref, self.ctx)
                val: PyValue = (
                    jval.to_python(
                        max_depth=max_depth - 1,
                        prefer_float=prefer_float,
                    )
                    if max_depth
                    else jval
                )
                pylist.append(val)

        return pylist

    @classmethod
    def from_list(
        cls,
        ctx: _stubs.JSContextRef,
        pylist: PyList,
        *,
        prefer_undefined: bool = False,
    ) -> Self:
        jval_refs = [
            cls.from_python(ctx, x, prefer_undefined=prefer_undefined).ref
            for x in pylist
        ]
        jvals_ptr = _ffi.new('JSValueRef[]', jval_refs)

        with js_error.scoped(ctx) as error_jval_ptr:
            jarray = _stubs.JSObjectMakeArray(
                ctx, len(jval_refs), jvals_ptr, error_jval_ptr
            )
        return cls(jarray, ctx)

    def to_python(
        self,
        *,
        max_depth: int = 5,  # TODO: make optional
        prefer_float: bool = False,
    ) -> PyValue:
        jtype = _stubs.JSValueGetType(self.ctx, self.ref)
        pyval: PyValue
        match jtype:
            case _stubs.kJSTypeUndefined | _stubs.kJSTypeNull:
                self.to_none()
                pyval = None
            case _stubs.kJSTypeString:
                pyval = self.to_str()
            case _stubs.kJSTypeNumber:
                pyval = self.to_float() if prefer_float else self.to_int()
            case _stubs.kJSTypeBoolean:
                pyval = self.to_bool()
            case _stubs.kJSTypeObject:
                pyval = (
                    self.to_list(
                        max_depth=max_depth,
                        prefer_float=prefer_float,
                    )
                    if _stubs.JSValueIsArray(self.ctx, self.ref)
                    else self.to_dict(
                        max_depth=max_depth,
                        prefer_float=prefer_float,
                    )
                )
            case _:
                raise NotImplementedError(f'Unsupported JavaScript type: {jtype}')
        return pyval

    @classmethod
    def from_python(
        cls,
        ctx: _stubs.JSContextRef,
        pyval: PyValue,
        *,
        prefer_undefined: bool = False,
    ) -> JSValue:
        """Converts a Python value into a corresponding JavaScript value."""
        if pyval is None:
            jval = cls.from_none(ctx, undefined=prefer_undefined)
        elif isinstance(pyval, JSValue):
            jval = pyval
        elif isinstance(pyval, bool):
            jval = cls.from_bool(ctx, pyval)
        elif isinstance(pyval, float):
            jval = cls.from_float(ctx, pyval)
        elif isinstance(pyval, int):
            jval = cls.from_int(ctx, pyval)
        elif isinstance(pyval, str):
            jval = cls.from_str(ctx, pyval)
        elif isinstance(pyval, PyDictAny):
            jval = cls.from_dict(ctx, pyval, prefer_undefined=prefer_undefined)
        elif isinstance(pyval, PyListAny):
            jval = cls.from_list(ctx, pyval, prefer_undefined=prefer_undefined)
        else:
            raise NotImplementedError(
                f'Unable to convert Python object into JavaScript: {pyval}'
            )
        return jval

    @contextmanager
    def scoped(self) -> Generator[Self, None, None]:
        """Context manager that automatically protects and unprotects a JS value."""
        _stubs.JSValueProtect(self.ctx, self.ref)
        try:
            yield self
        finally:
            _stubs.JSValueUnprotect(self.ctx, self.ref)

    @classmethod
    @contextmanager
    def scoped_from(
        cls,
        ctx: _stubs.JSContextRef,
        val: _stubs.JSValueRef | PyValue,
        *,
        prefer_undefined: bool = False,
    ) -> Generator[JSValue, None, None]:
        """Context manager that wraps a value as a temporarily protected JavaScript
        value reference, automatically unprotecting the JS value when the context exits.

        If the value is not already a JS value, then it's wrapped automatically.
        """
        jval = (
            cls.from_python(ctx, val, prefer_undefined=prefer_undefined)
            if isinstance(val, (JSValue, PyPrimitive, PyDictAny, PyListAny))
            else cls(val, ctx)
        )
        with jval.scoped():
            yield jval


from . import js_obj  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'JSValue',
]
