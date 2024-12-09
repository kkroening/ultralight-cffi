import contextlib
import ultralight_cffi as ultra


def test_JSObject__set_property__get_property(js_ctx):
    prop_name = 'sample_prop'
    expected_pyval = 'sample value'

    jobj_ref = ultra.JSContextGetGlobalObject(js_ctx.ref)
    jobj = ultra.JSObject(jobj_ref, js_ctx)

    jval = ultra.JSValue.new(js_ctx, expected_pyval)
    jobj.set_property(prop_name, jval)

    actual_pyval = jobj.get_property(prop_name).to_python()
    assert actual_pyval == expected_pyval


class Test_JSObject__new:
    def test__empty(self, faker, js_ctx):
        orig_count = js_ctx.get_protected_object_count()

        jobj = ultra.JSObject.new(js_ctx)
        assert jobj.get_property_names() == []

        assert js_ctx.get_protected_object_count() == orig_count + 1
        del jobj
        assert js_ctx.get_protected_object_count() == orig_count

    def test__simple(self, faker, js_ctx):
        pydict = {
            'key1': faker.lexify('pyval1-???'),
            'key2': faker.pybool(),
        }
        jobj = ultra.JSObject.new(js_ctx, pydict)
        assert jobj.get_property_names() == list(pydict.keys())
        assert jobj.get_property('key1').to_str() == pydict['key1']
        assert jobj.get_property('key2').to_bool() == pydict['key2']
        assert jobj.to_python() == pydict

    def test__from_ref(self, faker, js_ctx):
        orig_count = js_ctx.get_protected_object_count()
        jobj1 = ultra.JSObject.new(js_ctx)
        assert js_ctx.get_protected_object_count() == orig_count + 1

        assert ultra.JSObject.new(js_ctx, jobj1.ref) is jobj1

        # TBD: downgrading the JSObject to an equivalent JSValue drops protection.
        # (This behavior could be dangerous, if JSValues are retained without being
        # attached to the object graph and then accessed again after garbage collection.
        # Although there's a small amount of overhead to continuously protect/unprotect
        # values and maintain a mapping of JSValue Python objects, it may be negligible
        # in comparison to the safety risk of not extending protection to cover JSValues
        # but nonetheless it's the current expectation)
        jval1 = ultra.JSValue(jobj1.ref, js_ctx)
        del jobj1
        assert js_ctx.get_protected_object_count() == orig_count

        # Expectation - rematerializing the JSObject creates a new Python object since
        # the previous one was collected, but the same underlying JS obj still exists:
        jobj2 = ultra.JSObject(jval1.ref, js_ctx)
        assert js_ctx.get_protected_object_count() == orig_count + 1
        del jobj2
        assert js_ctx.get_protected_object_count() == orig_count

    def test__from_jval(self, faker, js_ctx):
        pass  # TODO: test (including re-creation)

    def test__nested_pydict(self, faker, js_ctx):
        nested_pydict = {'key1': faker.pyfloat(3, 3)}
        pydict = {'key2': nested_pydict}
        jobj = ultra.JSObject.new(js_ctx, pydict)
        assert jobj.get_property_names() == ['key2']
        assert jobj.get_property('key2').to_dict() == nested_pydict
        assert jobj.to_python() == pydict

    def test__nested_jobj(self, faker, js_ctx):
        nested_pydict = {'key1': faker.pyfloat(3, 3)}
        nested_jobj = ultra.JSObject.new(js_ctx, nested_pydict)
        pydict = {'key2': nested_jobj}
        jobj = ultra.JSObject.new(js_ctx, pydict)
        assert jobj.get_property_names() == ['key2']
        assert (
            jobj.get_property('key2').ref == nested_jobj.ref
        ), 'pointer must be preserved exactly'

    def test__nested_jarray(self, faker, js_ctx):
        nested_pyarray = [faker.lexify(), faker.lexify()]
        nested_jarray = ultra.JSValue.new(js_ctx, nested_pyarray)
        pydict = {'key2': nested_jarray}
        jobj = ultra.JSObject.new(js_ctx, pydict)
        assert jobj.get_property_names() == ['key2']
        assert (
            jobj.get_property('key2').ref == nested_jarray.ref
        ), 'pointer must be preserved exactly'


def test__class_example(js_ctx, lib):
    expected_message = 'Hello, world!'
    expected_function_result = 'Hello from static function!'

    @ultra.callback('JSObjectGetPropertyCallback')
    def get_static_prop(
        ctx_ref: ultra.JSContextRef,
        obj_ref: ultra.JSObjectRef,
        property_name_jstr: ultra.JSStringRef,
        error_jval_ref_ptr: ultra.Pointer[ultra.JSValueRef],
    ) -> ultra.JSValueRef:
        assert ctx_ref == js_ctx.ref
        return ultra.JSValue.new(js_ctx, expected_message).ref

    @ultra.callback('JSObjectCallAsFunctionCallback')
    def static_function_callback(
        ctx_ref: ultra.JSContextRef,
        func_obj_ref: ultra.JSObjectRef,
        this_obj_ref: ultra.JSObjectRef,
        argument_count: int,
        arguments: ultra.Pointer[ultra.JSValueRef],
        error_jval_ref_ptr: ultra.Pointer[ultra.JSValueRef],
    ) -> ultra.JSValueRef:
        assert ctx_ref == js_ctx.ref
        return ultra.JSValue.new(js_ctx, expected_function_result).ref

    @ultra.callback('JSObjectCallAsConstructorCallback')
    def ctor_callback(
        ctx_ref: ultra.JSContextRef,
        ctor_ref: ultra.JSObjectRef,
        argument_count: int,
        arguments: ultra.Pointer[ultra.JSValueRef],
        error_jval_ref_ptr: ultra.Pointer[ultra.JSValueRef],
    ) -> ultra.JSObjectRef:
        assert ctx_ref == js_ctx.ref
        return ultra.JSObjectMake(ctx_ref, jclass_ref, ultra.NULL)

    # Retain FFI pointers as Python references to prevent premature GC
    static_prop_name_ptr = ultra.new('char[]', b'staticProp')
    static_function_name_ptr = ultra.new('char[]', b'staticFunc')
    jclass_name_ptr = ultra.new('char[]', b'MyClass')

    jclass_static_values_ptr = ultra.new(
        'JSStaticValue[]',
        [
            {
                'name': static_prop_name_ptr,
                'getProperty': get_static_prop,
                'setProperty': ultra.NULL,
                'attributes': (
                    lib.kJSPropertyAttributeReadOnly
                    | lib.kJSPropertyAttributeDontDelete
                ),
            },
            {'name': ultra.NULL},
        ],
    )

    jclass_static_functions_ptr = ultra.new(
        'JSStaticFunction[]',
        [
            {
                'name': static_function_name_ptr,
                'callAsFunction': static_function_callback,
                'attributes': lib.kJSPropertyAttributeDontDelete,
            },
            {'name': ultra.NULL},
        ],
    )

    jclass_def_ptr = ultra.new('JSClassDefinition *', lib.kJSClassDefinitionEmpty)
    jclass_def = jclass_def_ptr[0]
    jclass_def.className = jclass_name_ptr
    jclass_def.staticValues = jclass_static_values_ptr
    jclass_def.staticFunctions = jclass_static_functions_ptr

    with contextlib.ExitStack() as exit_stack:
        jclass_ref = ultra.JSClassCreate(jclass_def_ptr)
        exit_stack.callback(ultra.JSClassRelease, jclass_ref)

        jctor_ref = ultra.JSObjectMakeConstructor(js_ctx.ref, jclass_ref, ctor_callback)
        jctor = ultra.JSObject.new(js_ctx, jctor_ref)
        js_ctx.get_global_obj().set_property('MyObj', jctor)

        arg_jvals_ref = ultra.new('JSValueRef[]', [])
        with ultra.js_error.scoped(js_ctx) as error_jobj_ref:
            jobj_ref = ultra.JSObjectCallAsConstructor(
                js_ctx.ref, jctor_ref, 0, arg_jvals_ref, error_jobj_ref
            )

        jobj = ultra.JSObject.new(js_ctx, jobj_ref)
        js_ctx.get_global_obj().set_property('myobj', jobj)

        def js_eval(txt):
            res = js_ctx.evaluate_script(txt)
            return res.to_python() if res is not None else None

        # js_eval('function throwError() { throw new Error("womp!") }; throwError()')

        actual_message = js_eval('myobj.staticProp')
        assert actual_message == expected_message

        actual_function_result = js_eval('myobj.staticFunc()')
        assert actual_function_result == expected_function_result
