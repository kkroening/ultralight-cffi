import contextlib
from .. import _ffi
from .. import _stubs
from . import js_error
from . import js_str
from . import js_val
from collections.abc import Callable
from typing import TypeAlias
from typing import cast

FunctionCallable: TypeAlias = Callable[
    [
        _stubs.JSContextRef,  # ctx
        _stubs.JSObjectRef,  # function
        _stubs.JSObjectRef,  # thisObject
        list[_stubs.JSValueRef],  # arguments
    ],
    _stubs.JSObjectRef,
]


def get_property(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
    prop_name: str,
) -> _stubs.JSValueRef:
    """Retrieves a property value from an Ultralight JavaScript object."""
    with js_str.scoped(prop_name) as prop_name_jstr:
        with js_error.scoped(ctx) as error_jval_ref:
            prop_value = _stubs.JSObjectGetProperty(
                ctx, jobj, prop_name_jstr, error_jval_ref
            )
    return prop_value


def set_property(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
    prop_name: str,
    value: _stubs.JSValueRef,
) -> None:
    """Sets a property on an Ultralight JavaScript object."""
    with js_str.scoped(prop_name) as prop_name_jstr:
        with js_error.scoped(ctx) as error_jval_ref:
            _stubs.JSObjectSetProperty(
                ctx,
                jobj,
                prop_name_jstr,
                value,
                0,
                error_jval_ref,
            )


def get_property_names(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
) -> list[str]:
    """Retrieves the names of all properties on a JavaScript object."""
    names_array = _stubs.JSObjectCopyPropertyNames(ctx, jobj)
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


def to_shallow_dict(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
) -> dict[str, _stubs.JSValueRef]:
    """Converts a JavaScript object into a Python dictionary shallowly - i.e. without
    recursively converting the values from :class:`JSValueRef` to Python values/objects.
    """
    return {k: get_property(ctx, jobj, k) for k in get_property_names(ctx, jobj)}


def new_function_from_script(
    ctx: _stubs.JSContextRef,
    name: str,
    param_names: list[str],
    script_body: str,
    *,
    source_url: str = '',
    starting_line_num: int = 0,
) -> _stubs.JSObjectRef:
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
            jobj = _stubs.JSObjectMakeFunction(
                ctx,
                name_jstr,
                len(param_names),
                param_names_jstrs,
                body_jstr,
                source_url_jstr,
                starting_line_num,
                error_jval_ref,
            )

    return jobj


def new_error(
    ctx: _stubs.JSContextRef,
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
    arg_jvals_ref = cast(
        _ffi.Pointer[_stubs.JSValueRef], _ffi.new('JSValueRef[]', arg_jvals)
    )

    with js_error.scoped(ctx) as nested_error_jobj_ref:
        error_jobj = _stubs.JSObjectMakeError(
            ctx,
            len(arg_jvals),
            arg_jvals_ref,
            nested_error_jobj_ref,
        )

    return error_jobj


def wrap_callable(
    func: FunctionCallable,
) -> _stubs.JSObjectCallAsFunctionCallback:
    """Wraps a Python callable as a CFFI callable that can be used as an Ultralight
    JavaScript function callback.

    Note:
        This is a low-level helper method, returning only a CFFI function pointer, which
        on its own is not directly callable from JavaScript.  To obtain a callable
        JavaScript function object, use :meth:`new_function_from_callable` instead.

    Warning:
        It's the caller's responsibility to ensure that the returned CFFI function
        pointer reference is retained for as long as there's any possibility that the
        function may be called - otherwise the function pointer will point to a deleted
        Python callable.

    Todo:
        Maybe have a failsafe `onerror` handler for the cffi callback because otherwise
        :class:`BaseException` errors such as :class:`KeyboardInterrupt` could
        potentially be delivered to the JS->Python callback while it's executing in
        Python, which is basically useless to return as a JS exception object, unless
        the JS execution environment were to somehow reliably propagate it all the way
        up the call chain, back into Python after passing through the JS call stack.

        The likelihood of such issues increases with the percentage of execution time
        spent inside of such JS->Python callbacks - rare in most cases but still
        something to be aware of and ideally fixed in the future.
    """

    @_ffi.callback('JSObjectCallAsFunctionCallback')
    def wrapper(
        ctx: _stubs.JSContextRef,
        function_jobj: _stubs.JSObjectRef,
        this_jobj: _stubs.JSObjectRef,
        arg_count: int,
        arg_jvals_ref: _ffi.Pointer[_stubs.JSValueRef],
        error_jval_ref: _ffi.Pointer[_stubs.JSValueRef],
    ) -> _stubs.JSValueRef:
        arg_jvals = _ffi.unpack(arg_jvals_ref, arg_count)

        try:
            result = func(ctx, function_jobj, this_jobj, arg_jvals)
        except Exception as error:  # pylint: disable=broad-except
            # TBD: Propagate exception back to JavaScript, after logging a Python
            # traceback.  It may be better to hard-fail all the way up the call chain
            # here though because if such an exception happens, it should probably be
            # considered fatal/non-recoverable.  "Expected" errors that are to be re-
            # raised in JS should come from a dedicated exception type with a clearly
            # defined way of representing the error as a JSValueRef.
            _ffi.logger.exception(
                'Exception in JS->Python callback; surface error from Python to JS'
            )

            error_message = f'Error in JS->Python callback: {str(error)}'
            with js_str.scoped(error_message) as error_message_jstr:
                error_message_jval = _stubs.JSValueMakeString(ctx, error_message_jstr)

            error_jval_ref[0] = new_error(ctx, [error_message_jval])
            result = _ffi.NULL  # TBD

        return result

    return wrapper


def new_function_from_callable(
    ctx: _stubs.JSContextRef,
    name: str,
    callback: FunctionCallable,
) -> tuple[_stubs.JSObjectRef, _stubs.JSObjectCallAsFunctionCallback]:
    """Creates a new JS function object from a Python callable, along with an associated
    wrapper CFFI function pointer.

    Warning:
        It's the caller's responsibility to ensure that the returned references are
        retained for as long as necessary to prevent premature garbage collection.

        Note that there are two distinct kinds of garbage collection to worry about:
        Python's garbage collection, and the JavaScript runtime's garbage collection.

        In the case of Python garbage collection, it's important to hold onto the CFI
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
    jcallback = wrap_callable(callback)
    with js_str.scoped(name) as name_jstr:
        jobj = _stubs.JSObjectMakeFunctionWithCallback(ctx, name_jstr, jcallback)
    return jobj, jcallback


__all__ = [
    'FunctionCallable',
    'get_property',
    'get_property_names',
    'new_error',
    'new_function_from_callable',
    'new_function_from_script',
    'set_property',
    'to_shallow_dict',
    'wrap_callable',
]
