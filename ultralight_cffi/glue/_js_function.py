from __future__ import annotations

import contextlib
import dataclasses
from .. import _ffi
from .. import _stubs
from . import _js_class
from . import _js_ctx
from . import _js_obj
from . import _js_val
from . import js_error
from . import js_str
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self
from typing import TypeAlias

FunctionCallable: TypeAlias = Callable[  # TODO: consolidate
    [
        _js_ctx.JSContext,  # ctx
        _stubs.JSObjectRef,  # function
        _stubs.JSObjectRef,  # thisObject
        list[_stubs.JSValueRef],  # arguments
    ],
    _stubs.JSObjectRef,
]


JSFunctionCallable: TypeAlias = Callable[
    [_js_obj.JSObject, _js_obj.JSObject, list[_js_val.JSValue]],
    _js_val.JSValue,
]


# @dataclass(frozen=True)
# class JSFunctionState:
#     handler: JSFunctionCallable


@dataclass(frozen=True)
class JSFunctionClass(_js_class.JSClass):
    _handler_map: dict[_stubs.JSObjectRef, JSFunctionCallable] = dataclasses.field(
        compare=False,
        default_factory=dict,
        repr=False,
    )
    """A mapping of instantiated JS object refs to corresponding handler functions.

    Note:
        It might seem odd to track this info on the :class:`JSFunctionClass` rather than
        having a subclass of :class:`JSObject` to represent function instances, but
        actually :class:`JSObject` is just a protected *view* of an object whose
        lifetime is owned by the JavaScript runtime.  The separation is a byproduct of
        the fundamental reality of integrating two different garbage collected runtimes
        (Python and JavaScript), and without such a separation there's a chicken and
        egg situation between the Python side deciding when to stop protecting a JS
        object reference so that the JS runtime can garbage collect the object, vs when
        the internal Python state data (handler function references, in this case) can
        be freed.  In other words, the :class:`JSObject` on the Python side needs to be
        destroyed before the underlying JavaScript object can potentially be finalized,
        which in turn causes :meth:`JSFunctionClass._finalize` to be fired, allowing the
        internal Python state to be released.
    """

    def instantiate(
        self,
        ctx: _js_ctx.JSContext,
        handler: JSFunctionCallable,
    ) -> _js_obj.JSObject:
        ref = _stubs.JSObjectMake(ctx.ref, self.ref, _ffi.NULL)
        self._handler_map[ref] = handler
        return _js_obj.JSObject.new(ctx, ref)

    def _finalize(
        self,
        obj_ref: _stubs.JSObjectRef,
    ) -> None:
        # TBD: this assert could be more lenient, but *shouldn't* ever fail, in theory
        assert obj_ref in self._handler_map, (
            f'Attempting to finalize a {type(self).__qualname__} instance missing from '
            'the internal state mapping'
        )
        del self._handler_map[obj_ref]

    def _call_as_function(
        self,
        func_obj: _js_obj.JSObject,
        this_obj: _js_obj.JSObject,
        arg_vals: list[_js_val.JSValue],
    ) -> _js_val.JSValue:
        assert func_obj.ref in self._handler_map, (
            f'Attempting to call a {type(self).__qualname__} instance missing from '
            'the internal state mapping'
        )
        handler = self._handler_map[func_obj.ref]
        return handler(func_obj, this_obj, arg_vals)


@dataclass(frozen=True)
class JSFunction(_js_obj.JSObject):  # pylint: disable=abstract-method
    @classmethod
    def new_from_script(
        cls,
        ctx: _js_ctx.JSContext,
        name: str,
        param_names: list[str],
        script_body: str,
        *,
        source_url: str = '',
        starting_line_num: int = 0,
    ) -> Self:
        """Creates a new JavaScript function object from a script body.

        Warning:
            It's the caller's responsibility to ensure that the resulting JS object is not
            prematurely garbage collected by the JavaScript runtime.
        """
        with contextlib.ExitStack() as exit_stack:
            name_jstr = exit_stack.enter_context(js_str.scoped(name))
            param_names_jstrs = _ffi.new(
                'JSStringRef[]',
                [exit_stack.enter_context(js_str.scoped(x)) for x in param_names],
            )
            body_jstr = exit_stack.enter_context(js_str.scoped(script_body))
            source_url_jstr = exit_stack.enter_context(js_str.scoped(source_url))

            with js_error.scoped(ctx) as error_jval_ref:
                jobj_ref = _stubs.JSObjectMakeFunction(
                    ctx.ref,
                    name_jstr,
                    len(param_names),
                    param_names_jstrs,
                    body_jstr,
                    source_url_jstr,
                    starting_line_num,
                    error_jval_ref,
                )

        return cls(jobj_ref, ctx)

    @staticmethod
    def wrap_callable(
        func: FunctionCallable,
    ) -> _stubs.JSObjectCallAsFunctionCallback:
        """Wraps a Python callable as a CFFI callable that can be used as an Ultralight
        JavaScript function callback.

        Note:
            This is a low-level helper method, returning only a CFFI function pointer,
            which on its own is not directly callable from JavaScript.  To obtain a
            callable JavaScript function object, use :meth:`new_function_from_callable`
            instead.

        Warning:
            It's the caller's responsibility to ensure that the returned CFFI function
            pointer reference is retained for as long as there's any possibility that
            the function may be called - otherwise the function pointer will point to a
            deleted Python callable.

        Todo:
            Maybe have a failsafe `onerror` handler for the cffi callback because
            otherwise :class:`BaseException` errors such as :class:`KeyboardInterrupt`
            could potentially be delivered to the JS->Python callback while it's
            executing in Python, which is basically useless to return as a JS exception
            object, unless the JS execution environment were to somehow reliably
            propagate it all the way up the call chain, back into Python after passing
            through the JS call stack.

            The likelihood of such issues increases with the percentage of execution
            time spent inside of such JS->Python callbacks - rare in most cases but
            still something to be aware of and ideally fixed in the future.
        """

        @_ffi.callback('JSObjectCallAsFunctionCallback')
        def wrapper(
            ctx_ref: _stubs.JSContextRef,
            function_jobj: _stubs.JSObjectRef,
            this_jobj: _stubs.JSObjectRef,
            arg_count: int,
            arg_jvals_ref: _ffi.Pointer[_stubs.JSValueRef],
            error_jval_ref: _ffi.Pointer[_stubs.JSValueRef],
        ) -> _stubs.JSValueRef:
            ctx = _js_ctx.JSContext(ctx_ref)
            try:
                arg_jvals = _ffi.unpack(arg_jvals_ref, arg_count)
                result = func(ctx, function_jobj, this_jobj, arg_jvals)
            except Exception as error:  # pylint: disable=broad-except
                # TBD: Propagate exception back to JavaScript, after logging a Python
                # traceback.  It may be better to hard-fail all the way up the call
                # chain here though because if such an exception happens, it should
                # probably be considered fatal/non-recoverable.  "Expected" errors that
                # are to be re-raised in JS should come from a dedicated exception type
                # with a clearly defined way of representing the error as a JSValueRef.
                _ffi.logger.exception(
                    'Exception in JS->Python callback; surface error from Python '
                    'to JS'
                )

                error_message = f'Error in JS->Python callback: {str(error)}'
                error_message_jval = _js_val.JSValue.new(ctx, error_message)
                error_jval_ref[0] = _js_obj.new_error(ctx, [error_message_jval]).ref
                result = _ffi.NULL

            return result

        return wrapper

    @classmethod
    def new_from_callable(
        cls,
        ctx: _js_ctx.JSContext,
        name: str,
        callback: FunctionCallable,
    ) -> tuple[_stubs.JSObjectRef, _stubs.JSObjectCallAsFunctionCallback]:
        """Creates a new JS function object from a Python callable, along with an
        associated wrapper CFFI function pointer.

        Warning:
            It's the caller's responsibility to ensure that the returned references are
            retained for as long as necessary to prevent premature garbage collection.

            Note that there are two distinct kinds of garbage collection to worry about:
            Python's garbage collection, and the JavaScript runtime's garbage
            collection.

            In terms of Python garbage collection, it's important to hold onto the CFI
            callback function pointer so that if the respective C function pointer gets
            called, it doesn't hit a dangling reference to a deleted Python callable.

            On the JavaScript garbage collection side, the resulting JS object needs to
            either be referenced by another object within the JS context's object graph
            (e.g. as a property on the global ``window``JS object), or by using
            :meth:`_stubs.JSValueProtect` to take explicit ownership on the Python side.
            See Ultralight's `Garbage-Collected Types`_ for more info.

        .. _Garbage-Collected Types:
            https://docs.ultralig.ht/docs/garbage-collected-types
        """
        jcallback = cls.wrap_callable(callback)
        with js_str.scoped(name) as name_jstr:
            jobj = _stubs.JSObjectMakeFunctionWithCallback(
                ctx.ref, name_jstr, jcallback
            )
        return jobj, jcallback


__all__ = [
    'FunctionCallable',
    'JSFunction',
]
