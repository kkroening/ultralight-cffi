import ultralight_cffi as ultra


def test_JSObject__set_property__get_property(js_ctx):
    prop_name = 'sample_prop'
    expected_pyval = 'sample value'

    jobj_ref = ultra.JSContextGetGlobalObject(js_ctx)
    jobj = ultra.JSObject(jobj_ref, js_ctx)

    jval = ultra.JSValue.new(js_ctx, expected_pyval)
    jobj.set_property(prop_name, jval)

    actual_pyval = jobj.get_property(prop_name).to_python()
    assert actual_pyval == expected_pyval


class Test_JSObject__new:
    def test__empty(self, faker, js_ctx):
        jobj = ultra.JSObject.new(js_ctx)
        assert jobj.get_property_names() == []

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
