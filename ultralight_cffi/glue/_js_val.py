from __future__ import annotations

import dataclasses
import math
from .. import _ffi
from .. import _stubs
from . import _js_ctx
from . import js_error
from . import js_str
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from types import TracebackType
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
    """Type alias for Python types that can trivially be converted to/from JavaScript.

    :class:`JSValue` is included in the type alias in order to allow for hybridized
    Python data that contains references to existing JavaScript values/objects - for
    example, a dict containing a list of :class:`JSValueRef` - which avoids having to
    always fully materialize JavaScript object graphs as Python data trees.
    """

else:
    PyDict = PyDictAny
    PyList = PyListAny
    PyValue: TypeAlias = Any


@dataclass(frozen=True)
class JSValue:
    ref: _stubs.JSValueRef
    ctx: _js_ctx.JSContext = dataclasses.field(repr=False)

    # __cached_js_type: _stubs.JSType | None = dataclasses.field(  # TODO/TBD
    #     compare=False, default=False, repr=False
    # )
    # """Purely internal cache value for the result of ``JSValueGetType`` to be used in
    # :meth:`is_str`, etc.
    # """

    def __str__(self) -> str:
        with js_error.scoped(self.ctx) as error_jval_ptr:
            jstr = _stubs.JSValueToStringCopy(
                self.ctx.ref,
                self.ref,
                error_jval_ptr,
            )
        if jstr == _ffi.NULL:
            pyval = 'NULL'  # TBD
        else:
            try:
                pyval = js_str.decode(jstr)
            finally:
                _stubs.JSStringRelease(jstr)
        return pyval

    def is_null(self) -> bool:
        return _stubs.JSValueIsNull(self.ctx.ref, self.ref)

    def is_undefined(self) -> bool:
        return _stubs.JSValueIsUndefined(self.ctx.ref, self.ref)

    def is_bool(self) -> bool:
        return _stubs.JSValueIsBoolean(self.ctx.ref, self.ref)

    def is_number(self) -> bool:
        return _stubs.JSValueIsNumber(self.ctx.ref, self.ref)

    def is_str(self) -> bool:
        return _stubs.JSValueIsString(self.ctx.ref, self.ref)

    def is_obj(self) -> bool:
        return _stubs.JSValueIsObject(self.ctx.ref, self.ref)

    def is_array(self) -> bool:
        return _stubs.JSValueIsArray(self.ctx.ref, self.ref)

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
                self.ctx.ref,
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
        if not self.is_null() and not self.is_undefined():
            raise TypeError(
                'Expected JavaScript value to be null or undefined: '
                f'{self.to_json_str("undefined")}'
            )

    @classmethod
    def _new_from_none(
        cls,
        ctx: _js_ctx.JSContext,
        *,
        undefined: bool = False,
    ) -> Self:
        """Creates a JavaScript null or undefined value representing a Python ``None``.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = (
            _stubs.JSValueMakeUndefined(ctx.ref)
            if undefined
            else _stubs.JSValueMakeNull(ctx.ref)
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
        if not strict and self.is_undefined():
            # JSValueToBoolean crashes with undefined values for some reason, despite
            # coercing other types based on truthiness.
            pyval = False
        elif strict and not self.is_bool():
            raise TypeError(
                'Expected JavaScript value to be a boolean: '
                + self.to_json_str('undefined')
            )
        else:
            pyval = _stubs.JSValueToBoolean(self.ctx.ref, self.ref)
        return pyval

    @classmethod
    def _new_from_bool(
        cls,
        ctx: _js_ctx.JSContext,
        value: bool,
    ) -> Self:
        """Creates a JavaScript boolean value from a Python :class:`bool`.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = _stubs.JSValueMakeBoolean(ctx.ref, value)
        return cls(ref, ctx)

    def to_float(
        self,
        *,
        strict: bool = True,
    ) -> float:
        """Converts a JavaScript number value into a Python :class:`float`."""
        if strict and not self.is_number():
            raise TypeError(
                'Expected JavaScript value to be a number: '
                + self.to_json_str('undefined')
            )
        with js_error.scoped(self.ctx) as error_jval_ptr:
            pyval = _stubs.JSValueToNumber(self.ctx.ref, self.ref, error_jval_ptr)
        return pyval

    @classmethod
    def _new_from_float(
        cls,
        ctx: _js_ctx.JSContext,
        value: float,
    ) -> Self:
        """Creates a JavaScript number value from a Python :class:`float`.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = _stubs.JSValueMakeNumber(ctx.ref, value)
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
    def _new_from_int(
        cls,
        ctx: _js_ctx.JSContext,
        value: int,
    ) -> Self:
        """Creates a JavaScript number value from a Python :class:`int`.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        ref = _stubs.JSValueMakeNumber(ctx.ref, float(value))
        return cls(ref, ctx)

    def to_str(
        self,
        *,
        strict: bool = True,
    ) -> str:
        """Converts a JavaScript string value into a Python :class:`str`."""

        if strict and not self.is_str():
            raise TypeError(
                'Expected JavaScript value to be a string: '
                + self.to_json_str('undefined')
            )

        with js_error.scoped(self.ctx) as error_jval_ptr:
            jstr_ref = _stubs.JSValueToStringCopy(
                self.ctx.ref, self.ref, error_jval_ptr
            )

        # Note: `JSValueToStringCopy` retains a reference, so avoid using
        # `js_str.scoped()` here, which would double-retain otherwise.
        try:
            pyval = js_str.decode(jstr_ref)
        finally:
            if jstr_ref != _ffi.NULL:
                _stubs.JSStringRelease(jstr_ref)

        return pyval

    @classmethod
    def _new_from_str(
        cls,
        ctx: _js_ctx.JSContext,
        pystr: str,
    ) -> Self:
        """Creates a JavaScript value from a Python string.

        Warning:
            The caller is responsible for protecting against garbage collection.
        """
        with js_str.scoped(pystr) as jstr:
            ref = _stubs.JSValueMakeString(ctx.ref, jstr)
        return cls(ref, ctx)

    def to_dict(
        self,
        *,
        max_depth: int = 5,  # TODO: make optional
        prefer_float: bool = True,
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

        if not self.is_obj():
            raise TypeError(
                'Expected JavaScript value to be an object: '
                + self.to_json_str('undefined')
            )
        if strict and self.is_array():
            # Array objects can technically be converted to a Python dict, but it's
            # likely not intentional, unless explicitly requested via `strict=False`.
            raise TypeError(
                'Expected JavaScript value to be a non-array object: '
                + self.to_json_str('undefined')
            )

        jobj = (
            self
            if isinstance(self, _js_obj.JSObject)
            else _js_obj.JSObject.new(self.ctx, self.ref)
        )
        shallow_dict = jobj.to_shallow_dict()
        return (
            {
                k: v.to_python(
                    max_depth=max_depth - 1,
                    prefer_float=prefer_float,
                )
                for k, v in shallow_dict.items()
            }
            if max_depth
            else cast(PyDict, shallow_dict)
        )

    @classmethod
    def _new_from_dict(
        cls,
        ctx: _js_ctx.JSContext,
        pydict: PyDict,
        # jcls: _stubs.JSClassRef | None = None,
        *,
        prefer_undefined: bool = False,
    ) -> _js_obj.JSObject:
        return _js_obj.JSObject.new(ctx, pydict, prefer_undefined=prefer_undefined)

    def to_list(
        self,
        *,
        prefer_float: bool = True,
        max_depth: int = 5,  # TODO: make optional
    ) -> PyList:
        """Converts a JavaScript object value into a Python list (recursively)."""
        if not self.is_array():
            raise TypeError(
                'Expected JavaScript value to be an array object: '
                + self.to_json_str('undefined')
            )

        pylist: list[PyValue] = []
        jarray = _js_obj.JSObject.new(self.ctx, self.ref)  # TODO: JSArray instead?
        for index_str, jval in jarray.to_shallow_dict().items():
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
    def _new_from_list(
        cls,
        ctx: _js_ctx.JSContext,
        pylist: PyList,
        *,
        prefer_undefined: bool = False,
    ) -> Self:
        jval_refs = [
            cls.new(ctx, x, prefer_undefined=prefer_undefined).ref for x in pylist
        ]
        jvals_ptr = _ffi.new('JSValueRef[]', jval_refs)

        with js_error.scoped(ctx) as error_jval_ptr:
            jarray_ref = _stubs.JSObjectMakeArray(
                ctx.ref, len(jval_refs), jvals_ptr, error_jval_ptr
            )
        return cls(jarray_ref, ctx)

    def to_obj(self) -> _js_obj.JSObject:
        if not self.is_obj():
            raise TypeError(
                'Expected JavaScript value to be an object: '
                + self.to_json_str('undefined')
            )
        return _js_obj.JSObject.new(self.ctx, self.ref)

    def to_python(  # TODO: `to_primitive` instead?
        self,
        *,
        # mapper: JSPyObjectMapper | None = None,  # defaults to context's obj mapper
        max_depth: int = 5,  # TODO: make optional
        prefer_float: bool = True,
    ) -> PyValue:
        jtype = _stubs.JSValueGetType(self.ctx.ref, self.ref)
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
                # TODO: use object mapper
                if self.is_array():
                    pyval = self.to_list(
                        max_depth=max_depth,
                        prefer_float=prefer_float,
                    )
                elif max_depth:
                    pyval = self.to_dict(
                        max_depth=max_depth,
                        prefer_float=prefer_float,
                    )
                else:
                    pyval = self.to_obj()
            case _:
                raise NotImplementedError(f'Unsupported JavaScript type: {jtype}')
        return pyval

    @classmethod
    def _new_from_python(
        cls,
        ctx: _js_ctx.JSContext,
        pyval: PyValue,
        *,
        prefer_undefined: bool = False,
    ) -> JSValue:
        """Converts a Python value into a corresponding JavaScript value."""
        if pyval is None:
            jval = cls._new_from_none(ctx, undefined=prefer_undefined)
        elif isinstance(pyval, JSValue):
            jval = pyval
        elif isinstance(pyval, bool):
            jval = cls._new_from_bool(ctx, pyval)
        elif isinstance(pyval, float):
            jval = cls._new_from_float(ctx, pyval)
        elif isinstance(pyval, int):
            jval = cls._new_from_int(ctx, pyval)
        elif isinstance(pyval, str):
            jval = cls._new_from_str(ctx, pyval)
        elif isinstance(pyval, PyDictAny):
            jval = cls._new_from_dict(ctx, pyval, prefer_undefined=prefer_undefined)
        elif isinstance(pyval, PyListAny):
            jval = cls._new_from_list(ctx, pyval, prefer_undefined=prefer_undefined)
        else:
            raise NotImplementedError(
                f'Unable to convert Python object into JavaScript: {pyval}'
            )
        return jval

    @classmethod
    def new(
        cls,
        # TODO: switch arg order for consistency
        ctx: _js_ctx.JSContext,
        val: _stubs.JSValueRef | PyValue,
        *,
        prefer_undefined: bool = False,
    ) -> JSValue:
        """Constructs a JavaScript value from a Python value or reference to existing
        JavaScript value.
        """
        return (
            cls._new_from_python(ctx, val, prefer_undefined=prefer_undefined)
            if isinstance(val, (JSValue, PyPrimitive, PyDictAny, PyListAny))
            else cls(val, ctx)
        )

    def __enter__(self) -> Self:
        _stubs.JSValueProtect(self.ctx.ref, self.ref)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        _stubs.JSValueUnprotect(self.ctx.ref, self.ref)

    def check_context(
        self,
        expected_context: _js_ctx.JSContext,
    ) -> None:
        if self.ctx.ref is not expected_context.ref:
            raise RuntimeError(
                '{self} belongs to incorrect context {self.ctx.ref} rather than '
                '{expected_context.ref}'
            )
        if self.ctx is not expected_context:
            # The expectation is that there's exactly one JSContext Python object for
            # each particular JSContextRef CFFI pointer; in other words, it's considered
            # to be an error for two JSContexts to have the same JSContextRef pointer.
            raise RuntimeError(
                '{self} belongs to duplicated context {expected_context}'
            )


from . import _js_obj  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'JSValue',
]
