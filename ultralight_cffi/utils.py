"""Experimental utility methods/functionality for using Ultralight more Pythonically.

This stuff will ideally be promoted to a less experimental status, but still distinct
from the raw CFFI stubs layer because it's not part of the underlying SDK per se, and
has its own subjective opinions on how to wrap the lower level library calls.

This could potentially become a library of its own that leverages :mod:`ultralight_cffi`
rather than extends it from within, but it's convenient to have it all in one library/
repo for practical reasons.
"""

import contextlib
from . import _base
from . import _bindings
from . import _ffi
from . import _stubs
from ._base import Pointer
from collections.abc import Callable
from collections.abc import Generator
from contextlib import contextmanager
from typing import TypeAlias
from typing import cast

JFunctionCallable: TypeAlias = Callable[
    [
        _stubs.JSContextRef,  # ctx
        _stubs.JSObjectRef,  # function
        _stubs.JSObjectRef,  # thisObject
        list[_stubs.JSValueRef],  # arguments
    ],
    _stubs.JSObjectRef,
]


class UltralightError(Exception):
    pass


class UltralightJSError(UltralightError):
    pass


@contextmanager
def ulstr_scope(
    pystr: str,
) -> Generator[_stubs.ULString, None, None]:
    ulstr = _stubs.ulCreateStringUTF8(pystr.encode(), len(pystr.encode()))
    try:
        yield ulstr
    finally:
        _stubs.ulDestroyString(ulstr)


def jstr_decode(
    jstr: _stubs.JSStringRef,
) -> str:
    str_ptr = _stubs.JSStringGetCharactersPtr(jstr)
    str_len = _stubs.JSStringGetLength(jstr)
    try:
        # Each UTF-16 character is 2 bytes
        buffer = _bindings.ffi.buffer(str_ptr, str_len * 2)
        buffer_view = buffer[:]
        assert isinstance(buffer_view, memoryview)  # FIXME/TBD
        result: str = buffer_view.decode('utf-16')  # type: ignore[attr-defined]
    except UnicodeDecodeError as error:
        raise ValueError(f'Failed to decode UTF-16 string: {error}') from error
    return result


@contextmanager
def handle_ul_error() -> Generator[Pointer[_stubs.ULString], None, None]:
    error_ulstr_ref = cast(Pointer[_stubs.ULString], _bindings.ffi.new('ULString *'))
    try:
        yield error_ulstr_ref
    finally:
        error_str = _stubs.ulStringGetData(error_ulstr_ref[0])
        if error_str:
            raise UltralightError(error_str)


@contextmanager
def handle_js_error(
    ctx: _stubs.JSContextRef,
) -> Generator[Pointer[_stubs.JSValueRef], None, None]:
    error_jval_ref = cast(Pointer[_stubs.JSValueRef], _bindings.ffi.new('JSValueRef *'))
    yield error_jval_ref
    error_jval = error_jval_ref[0]
    if error_jval:
        error_str = jval_to_str(ctx, error_jval)  # Warning: potentially recursive
        if error_str != '{}':
            raise UltralightJSError(error_str)


def jval_to_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    indent: int = 0,
) -> str:
    with handle_js_error(ctx) as error_jval_ref:  # Warning: potentially recursive
        jstr = _stubs.JSValueCreateJSONString(
            ctx,
            jval,
            indent,
            error_jval_ref,
        )
    return jstr_decode(jstr)


@contextmanager
def jstr_scope(text: str) -> Generator[_stubs.JSStringRef, None, None]:
    jstr = _stubs.JSStringCreateWithUTF8CString(text.encode())
    try:
        yield jstr
    finally:
        _stubs.JSStringRelease(jstr)


def jobj_get_property(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
    prop_name: str,
) -> _stubs.JSValueRef:
    with jstr_scope(prop_name) as prop_name_jstr:
        with handle_js_error(ctx) as error_jval_ref:
            prop_value = _stubs.JSObjectGetProperty(
                ctx, jobj, prop_name_jstr, error_jval_ref
            )
    return prop_value


def jobj_set_property(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
    prop_name: str,
    value: _stubs.JSValueRef,
) -> None:
    with jstr_scope(prop_name) as prop_name_jstr:
        with handle_js_error(ctx) as error_jval_ref:
            _stubs.JSObjectSetProperty(
                ctx,
                jobj,
                prop_name_jstr,
                value,
                0,
                error_jval_ref,
            )


def jobj_get_property_names(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
) -> list[str]:
    names_array = _stubs.JSObjectCopyPropertyNames(ctx, jobj)
    try:
        name_count = _stubs.JSPropertyNameArrayGetCount(names_array)
        name_jstrs = [
            _stubs.JSPropertyNameArrayGetNameAtIndex(names_array, i)
            for i in range(name_count)
        ]
        names = [jstr_decode(x) for x in name_jstrs]
    finally:
        _stubs.JSPropertyNameArrayRelease(names_array)
    return names


def jobj_to_dict(
    ctx: _stubs.JSContextRef,
    jobj: _stubs.JSObjectRef,
) -> dict[str, _stubs.JSObjectRef]:
    return {
        k: jobj_get_property(ctx, jobj, k) for k in jobj_get_property_names(ctx, jobj)
    }


def jobj_new_function_from_script(
    ctx: _stubs.JSContextRef,
    name: str,
    param_names: list[str],
    script_body: str,
    *,
    source_url: str = '',
    starting_line_num: int = 0,
) -> _stubs.JSObjectRef:
    with contextlib.ExitStack() as exit_stack:
        name_jstr = exit_stack.enter_context(jstr_scope(name))
        param_names_jstrs = _ffi.new(
            'JSStringRef[]',
            [exit_stack.enter_context(jstr_scope(x)) for x in param_names],
        )
        body_jstr = exit_stack.enter_context(jstr_scope(script_body))
        source_url_jstr = exit_stack.enter_context(jstr_scope(source_url))

        with handle_js_error(ctx) as error_jval_ref:
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


def jobj_make_error(
    ctx: _stubs.JSContextRef,
    arg_jvals: list[_stubs.JSValueRef],
) -> _stubs.JSObjectRef:
    """Creates a

    Note:
        It's technically possible to encounter a nested error in the process of
        constructing an error, in which case the nested error is raised as a Python
        exception, rather than returning an error JS object.

    Warning:
        It's the caller's responsibility to ensure that the resulting JS object is not
        prematurely garbage collected by the JavaScript runtime.
    """
    arg_jvals_ref = cast(
        Pointer[_stubs.JSValueRef], _ffi.new('JSValueRef[]', arg_jvals)
    )

    with handle_js_error(ctx) as nested_error_jobj_ref:
        error_jobj = _stubs.JSObjectMakeError(
            ctx,
            len(arg_jvals),
            arg_jvals_ref,
            nested_error_jobj_ref,
        )

    return error_jobj


def jobj_wrap_callable(
    func: JFunctionCallable,
) -> _stubs.JSObjectCallAsFunctionCallback:
    """Wraps a Python callable as a CFFI callable that can be used as an Ultralight
    JavaScript function callback.

    Note:
        This returns only a CFFI function pointer, which by itself is not directly
        callable from JavaScript.  To obtain the latter, use
        :meth:`jobj_new_function_from_callable`.

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

    @_base.callback('JSObjectCallAsFunctionCallback')
    def wrapper(
        ctx: _stubs.JSContextRef,
        function_jobj: _stubs.JSObjectRef,
        this_jobj: _stubs.JSObjectRef,
        arg_count: int,
        arg_jvals_ref: Pointer[_stubs.JSValueRef],
        error_jval_ref: Pointer[_stubs.JSValueRef],
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
            _base.logger.exception(
                'Exception in JS->Python callback; surface error from Python to JS'
            )

            error_message = f'Error in JS->Python callback: {str(error)}'
            with jstr_scope(error_message) as error_message_jstr:
                error_message_jval = _stubs.JSValueMakeString(ctx, error_message_jstr)

            error_jval_ref[0] = jobj_make_error(ctx, [error_message_jval])
            result = _base.NULL  # TBD

        return result

    return wrapper


def jobj_new_function_from_callable(
    ctx: _stubs.JSContextRef,
    name: str,
    callback: JFunctionCallable,
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
    jcallback = jobj_wrap_callable(callback)
    with jstr_scope(name) as name_jstr:
        jobj = _stubs.JSObjectMakeFunctionWithCallback(ctx, name_jstr, jcallback)
    return jobj, jcallback


__all__ = [
    'handle_js_error',
    'handle_ul_error',
    'JFunctionCallable',
    'jobj_get_property',
    'jobj_get_property_names',
    'jobj_make_error',
    'jobj_new_function_from_callable',
    'jobj_new_function_from_script',
    'jobj_set_property',
    'jobj_to_dict',
    'jobj_wrap_callable',
    'jstr_decode',
    'jstr_scope',
    'jval_to_str',
    'ulstr_scope',
    'UltralightError',
    'UltralightJSError',
]
