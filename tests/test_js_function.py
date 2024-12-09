import ultralight_cffi as ultra


def test_JSFunctionClass(js_ctx):
    def handle_call(
        func_obj: ultra.JSObject,
        this_obj: ultra.JSObject,
        arg_vals: list[ultra.JSValue],
    ) -> ultra.JSValue:
        print('handle_call', func_obj, this_obj, arg_vals)
        return ultra.JSValue.new(js_ctx, 'Hello world')

    func_cls = ultra.JSFunctionClass()
    func_obj = func_cls.instantiate(js_ctx, handle_call)
    js_ctx.get_global_obj().set_property('somefunc', func_obj)
    res = js_ctx.evaluate_script('somefunc()')
    print(res.to_python())
