from __future__ import annotations

import dataclasses
import traceback
import weakref
from .. import _ffi
from .. import _stubs
from . import _js_ctx
from . import _js_obj
from . import _js_val
from dataclasses import dataclass
from typing import ClassVar

_logger = _ffi.logger  # TBD


@dataclass(frozen=True)
class JSClass:
    name: str = ''
    """The name of the JSC class; defaults to the Python class's :attr:`__qualname__`."""

    _active_instances: ClassVar[set[JSClass]] = set()
    """A global (class variable) set of :class:`JSClass` instances that are actively in
    use - i.e. having at least one JSObject instance currently alive in the JSC runtime.

    The purpose of maintaining this as a class variable is to ensure that a
    :class:`JSClass` is not garbage collected on the Python side if there are any
    instances still lurking on the JavaScript side, because otherwise the dynamically
    generated CFFI callbacks would be freed prematurely and then JSC could end up
    invoking dangling function pointers, resulting in segfaults.

    The instance tracking is automatically hooked into the ``initialize`` and
    ``finalize`` callbacks of the :class:`_stubs.JSClassDefinition` passed to JSC.

    As soon as the class is instantiated by the JSC runtime, the class is added to the
    :attr:`_active_instances` and the object ref is added to :attr:`obj_refs`.  When an
    instance is finalized by the JSC runtime, the reference is removed from
    :attr:`obj_refs`; and when all instances are finalized, :attr:`obj_refs` becomes
    empty and the class is removed from :attr:`_active_instances`.
    """

    _obj_refs: set[_stubs.JSObjectRef] = dataclasses.field(
        compare=False,
        default_factory=set,
        repr=False,
    )

    ref: _stubs.JSClassRef = dataclasses.field(init=False)

    # Dynamically generated CFFI callbacks:
    _cb__initialize: _stubs.JSObjectInitializeCallback = dataclasses.field(
        compare=False,
        init=False,
        repr=False,
    )
    _cb__finalize: _stubs.JSObjectFinalizeCallback = dataclasses.field(
        compare=False,
        init=False,
        repr=False,
    )

    # _cb__has_property: _stubs.JSObjectHasPropertyCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )
    # _cb__get_property: _stubs.JSObjectGetPropertyCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )
    # _cb__set_property: _stubs.JSObjectSetPropertyCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )
    # _cb__delete_property: _stubs.JSObjectDeletePropertyCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )
    # _cb__get_property_names: _stubs.JSObjectGetPropertyNamesCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )

    _cb__call_as_function: _stubs.JSObjectCallAsFunctionCallback | None = (
        dataclasses.field(
            compare=False,
            init=False,
            repr=False,
        )
    )

    # _cb__call_as_constructor: _stubs.JSObjectCallAsConstructorCallback = (
    #     dataclasses.field(
    #         compare=False,
    #         init=False,
    #         repr=False,
    #     )
    # )
    # _cb__has_instance: _stubs.JSObjectHasInstanceCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )
    # _cb__convert_to_type: _stubs.JSObjectConvertToTypeCallback = dataclasses.field(
    #     compare=False,
    #     init=False,
    #     repr=False,
    # )

    _finalizer: weakref.finalize = dataclasses.field(
        compare=False,
        init=False,
        repr=False,
    )
    """A finalizer that calls :func:`JSClassRelease` when the last Python reference to
    this :class:`JSClass` goes away.

    Note:
        The :attr:`_active_instances` class variable ensures that the :class:`JSClass`
        won't be finalized until there are no more JSObject instances of this class
        existing in the JSC runtime.
    """

    def _initialize(
        self,
        obj: _js_obj.JSObject,
    ) -> None:
        """Handles initialization of an object of this class - to be customized by
        :class:`JSClass` subclasses.

        Note:
            For an chain of custom class inheritance, the :meth:`_initialize` method
            will be called for each :class:`JSClass` sequentially.
        """

    def _finalize(
        self,
        obj_ref: _stubs.JSObjectRef,
    ) -> None:
        """Handles finalization of an object of this class - to be customized by
        :class:`JSClass` subclasses.

        Warning:
            According to the JavaScriptCore C API documentation, the :class:`JSContext`
            must not be used while handling this event, in order to prevent inadvertent
            nested garbage collection and other concurrency issues:

                You must not call any function that may cause a garbage collection or an
                allocation of a garbage collected object from within a
                ``JSObjectFinalizeCallback``. This includes all functions that have a
                ``JSContextRef`` parameter.

            As such, this function receives only a raw :class:`JSObjectRef`
            reference rather than a full-fledged :class:`JSObject`.  This is also a
            consequence of the fact that if a :class:`JSObject` exists for a particular
            :class:`JSObjectRef`, then the JSC object is being protected via
            :func:`JSValueProtect`, which would prevent the object from being garbage
            collected anyways.
        """

    def _generate_cb__initialize(self) -> _stubs.JSObjectInitializeCallback:
        @_ffi.callback('JSObjectInitializeCallback')
        def _cb__initialize(
            ctx_ref: _stubs.JSContextRef,
            obj_ref: _stubs.JSObjectRef,
        ) -> None:
            # Register the instance in `_obj_refs` first, in case the the custom
            # `_initialize` handler raises an exception, in which case we'll have at
            # least recorded the fact that the JSC object exists, to avoid prematurely
            # collecting this JSClass.
            self._active_instances.add(self)
            self._obj_refs.add(obj_ref)

            ctx = _js_ctx.JSContext(ctx_ref)
            obj = _js_obj.JSObject.new(ctx, obj_ref)
            self._initialize(obj)

        return _cb__initialize

    def _generate_cb__finalize(self) -> _stubs.JSObjectFinalizeCallback:
        @_ffi.callback('JSObjectFinalizeCallback')
        def _cb__finalize(
            obj_ref: _stubs.JSObjectRef,
        ) -> None:
            # Unregister the instance from `_obj_refs` first, in case the custom
            # `_finalize` handler raises an exception so that we're not hanging onto
            # dangling JSObjectRef pointers forever - because even if this method fails,
            # JSC has made up its mind that the object is being finalized, whether we
            # like it or not.
            self._obj_refs.remove(obj_ref)
            if not self._obj_refs:
                self._active_instances.remove(self)

            self._finalize(obj_ref)

        return _cb__finalize

    def _call_as_function(
        self,
        func_obj: _js_obj.JSObject,
        this_obj: _js_obj.JSObject,
        arg_vals: list[_js_val.JSValue],
    ) -> _js_val.JSValue:
        """Handles an object of this class being called as a function - to be customized
        by :class:`JSClass` subclasses.

        If this method is not implemented by a subclass, then the JavaScriptCore runtime
        behavior is to forward the call to the parent class.  See
        ``JSCallbackObject::callImpl`` in JavaScriptCore's
        ``Source/API/JSCallbackObjectFunctions.h``.
        """
        raise NotImplementedError()

    def _generate_cb__call_as_function(self) -> _stubs.JSObjectCallAsFunctionCallback:
        @_ffi.callback('JSObjectCallAsFunctionCallback')
        def _cb__call_as_function(
            ctx_ref: _stubs.JSContextRef,
            func_ref: _stubs.JSObjectRef,
            this_ref: _stubs.JSObjectRef,
            arg_count: int,
            arg_refs_ptr: _ffi.Pointer[_stubs.JSValueRef],
            error_ref_ptr: _ffi.Pointer[_stubs.JSValueRef],
        ) -> _stubs.JSValueRef:
            ctx = _js_ctx.JSContext(ctx_ref)

            try:
                func_obj = _js_obj.JSObject.new(ctx, func_ref)
                this_obj = _js_obj.JSObject.new(ctx, this_ref)
                arg_refs = arg_refs_ptr[0:arg_count]
                arg_vals = [_js_val.JSValue.new(ctx, x) for x in arg_refs]
                result_val = self._call_as_function(func_obj, this_obj, arg_vals)

            except Exception as error:  # pylint: disable=broad-except
                message = f'Error in {type(self).__qualname__} callAsFunction callback'

                # TODO: move to helper function:
                message_val = _js_val.JSValue.new(ctx, message)
                result_val = _js_val.JSValue.new(ctx, None)
                options_val = _js_obj.JSObject.new(
                    ctx,
                    dict(
                        cause=dict(
                            message=f'{type(error).__qualname__}: {str(error)}',
                            traceback=traceback.format_exc(),
                        ),
                    ),
                )
                error_obj = _js_obj.new_error(ctx, [message_val, options_val])
                error_ref_ptr[0] = error_obj.ref

            return result_val.ref

        return _cb__call_as_function

    @property
    def has_call_as_function(self) -> bool:
        """Whether or not this :class:`JSClass` implementation defines a custom
        :meth:`_call_as_function`.
        """
        return type(self)._call_as_function is not JSClass._call_as_function

    @classmethod
    def _py_finalize(cls, ref: _stubs.JSClassRef) -> None:
        """Handles finalization of the Python :class:`JSClass`.

        This is a fundamentally different kind of finalization that the JavaScript
        object finalization of :meth:`_finalize`, which corresponds to the ``finalize``
        callback of :class:`JSClassDefinition` in JavaScriptCore for finalizing a
        JavaScript object.  Rather, in this case the thing being finalized is the
        :class:`JSClass` *Python* object, when all Python references to this object go
        away.

        When this method is called, it means that there are no longer any (strong)
        references to this Python object, and thus the underlying JSC
        :class:`JSClassRef` can be released.
        """
        _logger.debug('%s releasing %r', cls.__qualname__, ref)
        # print(cls.__qualname__, 'releasing', ref)
        _stubs.JSClassRelease(ref)

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, 'name', type(self).__qualname__)

        # Generate CFFI callbacks; avoid setting non-implemented callbacks
        object.__setattr__(self, '_cb__initialize', self._generate_cb__initialize())
        object.__setattr__(self, '_cb__finalize', self._generate_cb__finalize())
        object.__setattr__(
            self,
            '_cb__call_as_function',
            (
                self._generate_cb__call_as_function()
                if self.has_call_as_function
                else None
            ),
        )

        # Define JSClassDefinition structure
        jclass_name_ptr = _ffi.new('char[]', self.name.encode())
        jclass_def_ptr = _ffi.new('JSClassDefinition *')
        jclass_def = jclass_def_ptr[0]
        jclass_def.className = jclass_name_ptr
        jclass_def.initialize = self._cb__initialize
        jclass_def.finalize = self._cb__finalize
        if self._cb__call_as_function is not None:
            jclass_def.callAsFunction = self._cb__call_as_function

        # Create the JSClass in JSC
        ref = _stubs.JSClassCreate(jclass_def_ptr)
        object.__setattr__(self, 'ref', ref)

        # Set up a finalizer for the Python object to release the underlying JSC class
        object.__setattr__(
            self, '_finalizer', weakref.finalize(self, self._py_finalize, self.ref)
        )
