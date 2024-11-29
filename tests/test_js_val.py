import json
import pytest
import ultralight_cffi as ultra


def test_to_json_str__conversions(faker, js_ctx):
    actual = ultra.js_val.to_json_str(js_ctx, ultra.NULL)
    assert actual == 'null'

    null_jval = ultra.js_val.from_none(js_ctx)
    actual = ultra.js_val.to_json_str(js_ctx, null_jval)
    assert actual == 'null'

    undefined_jval = ultra.js_val.from_none(js_ctx)
    actual = ultra.js_val.to_json_str(js_ctx, undefined_jval)
    assert actual == 'null'

    int_pyval = faker.pyint()
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_json_str(js_ctx, int_jval)
    assert actual == str(int_pyval)

    float_pyval = 3.14
    float_jval = ultra.js_val.from_float(js_ctx, float_pyval)
    actual = ultra.js_val.to_json_str(js_ctx, float_jval)
    assert actual == str(float_pyval)

    str_pyval = 'sample str'
    with ultra.js_val.scoped(js_ctx, str_pyval) as str_jval:
        actual = ultra.js_val.to_json_str(js_ctx, str_jval)
    assert actual == json.dumps(str_pyval)


def test_from_none__to_none(faker, js_ctx):
    null_jval = ultra.js_val.from_none(js_ctx)
    assert ultra.JSValueIsNull(js_ctx, null_jval) is True
    assert ultra.JSValueIsUndefined(js_ctx, null_jval) is False
    actual = ultra.js_val.to_none(js_ctx, null_jval)
    assert actual is None

    undefined_jval = ultra.js_val.from_none(js_ctx, undefined=True)
    assert ultra.JSValueIsNull(js_ctx, undefined_jval) is False
    assert ultra.JSValueIsUndefined(js_ctx, undefined_jval) is True
    actual = ultra.js_val.to_none(js_ctx, undefined_jval)
    assert actual is None

    str_pyval = faker.sentence()
    str_jval = ultra.js_val.from_str(js_ctx, str_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_none(js_ctx, str_jval)
    assert (
        str(excinfo.value)
        == f'Expected JavaScript value to be null or undefined: {json.dumps(str_pyval)}'
    )


def test_from_bool__to_bool(faker, js_ctx):
    # Scenario - false:
    bool_jval = ultra.js_val.from_bool(js_ctx, False)
    actual = ultra.js_val.to_bool(js_ctx, bool_jval)
    assert actual is False

    # Scenario - true:
    bool_jval = ultra.js_val.from_bool(js_ctx, True)
    actual = ultra.js_val.to_bool(js_ctx, bool_jval)
    assert actual is True

    # Scenario - null (strict):
    null_jval = ultra.js_val.from_none(js_ctx)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, null_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: null'

    # Scenario - undefined (strict):
    undefined_jval = ultra.js_val.from_none(js_ctx, undefined=True)
    assert ultra.JSValueIsUndefined(js_ctx, undefined_jval) is True
    # with pytest.raises(TypeError) as excinfo:  # TODO
    #     ultra.js_val.to_bool(js_ctx, undefined_jval)
    # assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: undefined'

    # Scenario - falsy string (strict):
    falsy_str_jval = ultra.js_val.from_str(js_ctx, '')
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, falsy_str_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: ""'

    # Scenario - truthy string (strict):
    truthy_str_pyval = faker.sentence()
    truthy_str_jval = ultra.js_val.from_str(js_ctx, truthy_str_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, truthy_str_jval)
    assert (
        str(excinfo.value)
        == f'Expected JavaScript value to be a boolean: "{truthy_str_pyval}"'
    )

    # Scenario - null/undefined (non-strict):
    actual = ultra.js_val.to_bool(js_ctx, null_jval, strict=False)
    assert actual is False
    actual = ultra.js_val.to_bool(js_ctx, undefined_jval, strict=False)
    assert actual is False

    # Scenario - falsy number (non-strict):
    int_pyval = 0
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_bool(js_ctx, int_jval, strict=False)
    assert actual is False

    # Scenario - truthy number (non-strict):
    int_pyval = faker.pyint(1, 100)
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_bool(js_ctx, int_jval, strict=False)
    assert actual is True

    # Scenario - falsy string (non-strict):
    actual = ultra.js_val.to_bool(js_ctx, falsy_str_jval, strict=False)
    assert actual is False

    # Scenario - truthy number (non-strict):
    actual = ultra.js_val.to_bool(js_ctx, truthy_str_jval, strict=False)
    assert actual is True


def test_from_float__to_float():
    pass  # TODO: test


def test_from_int__to_int():
    pass  # TODO: test


def test_from_str__to_str(faker, js_ctx):
    str_pyval = faker.sentence()
    str_jval = ultra.js_val.from_str(js_ctx, str_pyval)
    actual = ultra.js_val.to_str(js_ctx, str_jval)
    assert actual == str_pyval

    null_jval = ultra.js_val.from_none(js_ctx)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_str(js_ctx, null_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a string: null'

    int_pyval = faker.pyint()
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_str(js_ctx, int_jval)
    assert (
        str(excinfo.value) == f'Expected JavaScript value to be a string: {int_pyval}'
    )

    actual = ultra.js_val.to_str(js_ctx, int_jval, strict=False)
    assert actual == str(int_pyval)


def test_from_python__to_python():
    pass  # TODO: test


def test_scoped():
    pass  # TODO: test
