import ultralight_cffi as ultra


def test_get_property(js_ctx):
    # jcls_def_ref = ultra.new('JSClassDefinition *', [lib.kJSClassDefinitionEmpty])
    # jcls = ultra.JSClassCreate(jcls_def_ref)
    # exit_stack.callback(ultra.JSClassRelease, jcls)

    global_jobj = ultra.JSContextGetGlobalObject(js_ctx)
    global_dict = ultra.js_obj.to_shallow_dict(js_ctx, global_jobj)

    prop_name = 'sample_prop'
    expected_value = 'sample value'
    ultra.js_obj.set_property(
        js_ctx,
        global_jobj,
        prop_name,
        ultra.JSValue.from_str(js_ctx, expected_value).ref,
    )
    print(global_dict)
    with ultra.JSValue.scoped_from(
        js_ctx, ultra.js_obj.get_property(js_ctx, global_jobj, prop_name)
    ) as actual_jval:
        actual_value = actual_jval.to_str()
        assert actual_value == expected_value
