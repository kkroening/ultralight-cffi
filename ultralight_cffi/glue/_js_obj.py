from __future__ import annotations

import dataclasses
import weakref
from .. import _ffi
from .. import _stubs
from . import _js_ctx
from . import _js_val
from . import js_error
from . import js_str
from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import ClassVar
from typing import Self


@dataclass(frozen=True)
class JSObject(_js_val.JSValue):
    _weak_mapping: ClassVar[MutableMapping[_stubs.JSObjectRef, JSObject]] = (
        weakref.WeakValueDictionary()
    )

    ref: _stubs.JSObjectRef
    ctx: _js_ctx.JSContext = dataclasses.field(repr=False)

    _finalizer: weakref.finalize = dataclasses.field(
        repr=False, compare=False, init=False
    )

    def __post_init__(self) -> None:
        if not self.is_obj():
            # The caller somehow constructed a JSObject instance from a reference that's
            # not actually an object; maybe it's at least a JSValue that can be
            # serialized as JSON for an error message.
            jval = _js_val.JSValue(self.ref, self.ctx)
            raise TypeError(
                'Expected JavaScript value to be an object: '
                + jval.to_json_str('undefined')
            )

        if self.ref in self._weak_mapping:
            raise RuntimeError('Previously mapped JavaScript object already exists')

        self._weak_mapping[self.ref] = self
        _stubs.JSValueProtect(self.ctx.ref, self.ref)
        object.__setattr__(
            self,
            '_finalizer',
            weakref.finalize(self, _stubs.JSValueUnprotect, self.ctx.ref, self.ref),
        )

    def get_property(
        self,
        prop_name: str,
    ) -> _js_val.JSValue:
        """Retrieves a property value from an Ultralight JavaScript object."""
        with js_str.scoped(prop_name) as prop_name_jstr:
            with js_error.scoped(self.ctx) as error_jval_ref:
                prop_jval_ref = _stubs.JSObjectGetProperty(
                    self.ctx.ref, self.ref, prop_name_jstr, error_jval_ref
                )
        return _js_val.JSValue(prop_jval_ref, self.ctx)

    def set_property(
        self,
        prop_name: str,
        value: _js_val.JSValue,
    ) -> None:
        """Sets a property on an Ultralight JavaScript object."""
        assert value.ctx.ref == self.ctx.ref
        with js_str.scoped(prop_name) as prop_name_jstr:
            with js_error.scoped(self.ctx) as error_jval_ref:
                _stubs.JSObjectSetProperty(
                    self.ctx.ref,
                    self.ref,
                    prop_name_jstr,
                    value.ref,
                    0,
                    error_jval_ref,
                )

    def get_property_names(self) -> list[str]:
        """Retrieves the names of all properties on a JavaScript object."""
        names_array = _stubs.JSObjectCopyPropertyNames(self.ctx.ref, self.ref)
        try:
            name_count = _stubs.JSPropertyNameArrayGetCount(names_array)
            name_jstrs = [
                _stubs.JSPropertyNameArrayGetNameAtIndex(names_array, i)
                for i in range(name_count)
            ]
            names = [js_str.decode(x) for x in name_jstrs]
        finally:
            _stubs.JSPropertyNameArrayRelease(names_array)
        return names

    def to_shallow_dict(self) -> dict[str, _js_val.JSValue]:
        """Converts a JavaScript object into a Python dictionary shallowly - i.e.
        without recursively converting the values from :class:`JSValueRef` /
        :class:`JSValue` to Python values/objects.
        """
        return {k: self.get_property(k) for k in self.get_property_names()}

    @classmethod
    def new(  # pylint: disable=dangerous-default-value
        cls,
        # TODO: switch arg order for consistency
        ctx: _js_ctx.JSContext,
        val: _stubs.JSValueRef | _js_val.PyValue = {},
        *,
        prefer_undefined: bool = False,  # TBD
    ) -> Self:
        """Constructs a JavaScript object from a Python dict/mapping or reference to
        existing JavaScript object.
        """
        if isinstance(val, _js_val.JSValue):
            val.check_context(ctx)
            ref = val.ref
        elif (
            isinstance(val, _ffi.CData)
            and _ffi.typeof(val).cname == 'struct OpaqueJSValue *'
        ):
            ref = val
        else:
            ref = None

        if ref is not None:
            # TODO: map to expected subclass
            existing_jobj = cls._weak_mapping.get(ref)
            if existing_jobj is None:
                jobj = cls(ref, ctx)
                cls._weak_mapping[ref] = jobj
            elif not isinstance(existing_jobj, cls):
                raise TypeError(
                    f'Previously mapped JavaScript object has unexpected type '
                    f'{type(existing_jobj).__qualname__} rather than {cls.__qualname__}'
                )
            else:
                jobj = existing_jobj

        elif isinstance(val, _js_val.PyDictAny):
            jobj_ref = _stubs.JSObjectMake(ctx.ref, _ffi.NULL, _ffi.NULL)
            jobj = cls(jobj_ref, ctx)
            for key, pyval in val.items():
                with _js_val.JSValue.new(
                    ctx, pyval, prefer_undefined=prefer_undefined
                ) as jval:
                    jobj.set_property(key, jval)

        else:
            raise TypeError(
                f'{cls.__qualname__}.new requires either a Python dict/mapping or an '
                'existing JavaScript object (JSValue/JSValueRef); got '
                f'{type(val).__qualname__} instance'
            )

        return jobj

    @classmethod
    def _new_from_none(
        cls,
        ctx: _js_ctx.JSContext,
        *,
        undefined: bool = False,
    ) -> Self:
        raise NotImplementedError()

    @classmethod
    def _new_from_bool(
        cls,
        ctx: _js_ctx.JSContext,
        value: bool,
    ) -> Self:
        raise NotImplementedError()

    @classmethod
    def _new_from_float(
        cls,
        ctx: _js_ctx.JSContext,
        value: float,
    ) -> Self:
        raise NotImplementedError()

    @classmethod
    def _new_from_int(
        cls,
        ctx: _js_ctx.JSContext,
        value: int,
    ) -> Self:
        raise NotImplementedError()

    @classmethod
    def _new_from_str(
        cls,
        ctx: _js_ctx.JSContext,
        pystr: str,
    ) -> Self:
        raise NotImplementedError()

    @classmethod
    def _new_from_list(
        cls,
        ctx: _js_ctx.JSContext,
        pylist: _js_val.PyList,
        *,
        prefer_undefined: bool = False,
    ) -> Self:
        raise NotImplementedError()


def new_error(
    ctx: _js_ctx.JSContext,
    arg_jvals: list[_stubs.JSValueRef],
) -> _stubs.JSObjectRef:
    """Creates a new JavaScript Error object.

    Note:
        It's technically possible to encounter a nested error in the process of
        constructing an error, in which case the nested error is raised as a Python
        exception, rather than returning an error JS object.

    Warning:
        It's the caller's responsibility to ensure that the resulting JS object is not
        prematurely garbage collected by the JavaScript runtime.
    """
    arg_jvals_ref = _ffi.new('JSValueRef[]', arg_jvals)
    with js_error.scoped(ctx) as nested_error_jobj_ref:
        error_jobj = _stubs.JSObjectMakeError(
            ctx.ref,
            len(arg_jvals),
            arg_jvals_ref,
            nested_error_jobj_ref,
        )
    return error_jobj


__all__ = [
    'JSObject',
    'new_error',
]
