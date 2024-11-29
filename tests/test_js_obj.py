import contextlib
import ultralight_cffi as ultra


def test_get_property(lib):
    with contextlib.ExitStack() as exit_stack:
        # jcls_def_ref = ultra.new('JSClassDefinition *', [lib.kJSClassDefinitionEmpty])
        # jcls = ultra.JSClassCreate(jcls_def_ref)
        # exit_stack.callback(ultra.JSClassRelease, jcls)

        ctx = ultra.JSGlobalContextCreate(ultra.NULL)
        exit_stack.callback(ultra.JSGlobalContextRelease, ctx)

        global_jobj = ultra.JSContextGetGlobalObject(ctx)
        global_dict = ultra.js_obj.to_shallow_dict(ctx, global_jobj)

        prop_name = 'sample_prop'
        expected_value = 'sample value'
        ultra.js_obj.set_property(
            ctx, global_jobj, prop_name, ultra.js_val.from_str(ctx, expected_value)
        )
        print(global_dict)
        actual_jval = ultra.js_obj.get_property(ctx, global_jobj, prop_name)
        actual_value = ultra.js_val.to_str(ctx, actual_jval)
        assert actual_value == expected_value

    # assert 0
