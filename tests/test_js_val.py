import json
import math
import pytest
import ultralight_cffi as ultra


def test_to_json_str__conversions(faker, js_ctx):
    actual = ultra.js_val.to_json_str(js_ctx, ultra.NULL)
    assert actual == 'null'

    null_jval = ultra.js_val.from_none(js_ctx)
    actual = ultra.js_val.to_json_str(js_ctx, null_jval)
    assert actual == 'null'

    undefined_jval = ultra.js_val.from_none(js_ctx, undefined=True)
    actual = ultra.js_val.to_json_str(js_ctx, undefined_jval)
    assert actual is None

    bool_jval = ultra.js_val.from_bool(js_ctx, True)
    actual = ultra.js_val.to_json_str(js_ctx, bool_jval)
    assert actual == 'true'

    float_pyval = 3.14  # low precision to avoid JSON discrepancies
    float_jval = ultra.js_val.from_float(js_ctx, float_pyval)
    actual = ultra.js_val.to_json_str(js_ctx, float_jval)
    assert actual == str(float_pyval)

    int_pyval = faker.pyint()
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_json_str(js_ctx, int_jval)
    assert actual == str(int_pyval)

    str_pyval = 'sample str'
    with ultra.js_val.scoped(js_ctx, str_pyval) as str_jval:
        actual = ultra.js_val.to_json_str(js_ctx, str_jval)
    assert actual == json.dumps(str_pyval)


def test_from_none__to_none(faker, js_ctx):
    # Scenario - null:
    null_jval = ultra.js_val.from_none(js_ctx)
    assert ultra.JSValueIsNull(js_ctx, null_jval) is True
    assert ultra.JSValueIsUndefined(js_ctx, null_jval) is False
    actual = ultra.js_val.to_none(js_ctx, null_jval)
    assert actual is None

    # Scenario - undefined:
    undefined_jval = ultra.js_val.from_none(js_ctx, undefined=True)
    assert ultra.JSValueIsNull(js_ctx, undefined_jval) is False
    assert ultra.JSValueIsUndefined(js_ctx, undefined_jval) is True
    actual = ultra.js_val.to_none(js_ctx, undefined_jval)
    assert actual is None

    # Scenario - str:
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

    # Scenario - null coercion:
    null_jval = ultra.js_val.from_none(js_ctx)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, null_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: null'
    actual = ultra.js_val.to_bool(js_ctx, null_jval, strict=False)
    assert actual is False

    # Scenario - undefined coercion:
    undefined_jval = ultra.js_val.from_none(js_ctx, undefined=True)
    assert ultra.JSValueIsUndefined(js_ctx, undefined_jval) is True
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, undefined_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: None'
    actual = ultra.js_val.to_bool(js_ctx, undefined_jval, strict=False)
    assert actual is False

    # Scenario - falsy number coercion:
    int_pyval = 0
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_bool(js_ctx, int_jval, strict=False)
    assert actual is False

    # Scenario - truthy number coercion:
    int_pyval = faker.pyint(1, 100)
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_bool(js_ctx, int_jval, strict=False)
    assert actual is True

    # Scenario - nan coercion:
    nan_pyval = float('nan')
    nan_jval = ultra.js_val.from_float(js_ctx, nan_pyval)
    actual = ultra.js_val.to_bool(js_ctx, nan_jval, strict=False)
    assert actual is False

    # Scenario - falsy string coercion:
    falsy_str_jval = ultra.js_val.from_str(js_ctx, '')
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, falsy_str_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: ""'
    actual = ultra.js_val.to_bool(js_ctx, falsy_str_jval, strict=False)
    assert actual is False

    # Scenario - "false" string coercion:
    false_str_jval = ultra.js_val.from_str(js_ctx, 'false')
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, false_str_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: "false"'
    actual = ultra.js_val.to_bool(js_ctx, false_str_jval, strict=False)
    assert actual is True

    # Scenario - truthy string coercion:
    truthy_str_pyval = faker.sentence()
    truthy_str_jval = ultra.js_val.from_str(js_ctx, truthy_str_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_bool(js_ctx, truthy_str_jval)
    assert (
        str(excinfo.value)
        == f'Expected JavaScript value to be a boolean: "{truthy_str_pyval}"'
    )
    actual = ultra.js_val.to_bool(js_ctx, truthy_str_jval, strict=False)
    assert actual is True


def test_from_float__to_float(faker, js_ctx):
    # Scenario - float:
    float_pyval = 3.14
    float_jval = ultra.js_val.from_float(js_ctx, float_pyval)
    actual = ultra.js_val.to_float(js_ctx, float_jval)
    assert actual == float_pyval

    # Scenario - string coercion:
    str_pyval = faker.sentence()
    str_jval = ultra.js_val.from_str(js_ctx, str_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_float(js_ctx, str_jval)
    assert (
        str(excinfo.value) == f'Expected JavaScript value to be a number: "{str_pyval}"'
    )

    # Scenario - float coercion:
    str_jval = ultra.js_val.from_str(js_ctx, str_pyval)
    actual = ultra.js_val.to_float(js_ctx, str_jval, strict=False)
    assert math.isnan(actual)

    # TODO: more scenarios


def test_from_int__to_int(faker, js_ctx):
    # Scenario - int:
    int_pyval = faker.pyint(1, 1000)
    int_jval = ultra.js_val.from_int(js_ctx, int_pyval)
    actual = ultra.js_val.to_int(js_ctx, int_jval)
    assert actual == int_pyval

    # Scenario - bool coercion:
    bool_pyval = True
    bool_jval = ultra.js_val.from_bool(js_ctx, bool_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_int(js_ctx, bool_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a number: true'
    actual = ultra.js_val.to_int(js_ctx, bool_jval, strict=False)
    assert actual == int(bool_pyval)

    # Scenario - float coercion:
    float_pyval = int_pyval + 0.8  # >0.5 confirms truncation rather than rounding
    float_jval = ultra.js_val.from_float(js_ctx, float_pyval)
    actual = ultra.js_val.to_int(js_ctx, float_jval)
    assert actual == int(float_pyval)

    # Scenario - stringified bool coercion failure:
    # (Even in non-strict mode, strings that can't be converted to numbers are
    # considered to be an error)
    str_pyval = 'true'
    str_jval = ultra.js_val.from_str(js_ctx, str_pyval)
    with pytest.raises(ValueError) as excinfo:
        ultra.js_val.to_int(js_ctx, str_jval, strict=False)
    assert str(excinfo.value) == f'Cannot convert NaN to int: "{str_pyval}"'

    # Scenario - stringified integer:
    str_int_pyval = str(int_pyval)
    str_int_jval = ultra.js_val.from_str(js_ctx, str_int_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_int(js_ctx, str_int_jval)
    assert (
        str(excinfo.value)
        == f'Expected JavaScript value to be a number: "{str_int_pyval}"'
    )
    actual = ultra.js_val.to_int(js_ctx, str_int_jval, strict=False)
    assert actual == int_pyval

    # Scenario - stringified float coercion:
    str_float_pyval = str(float_pyval)
    str_float_jval = ultra.js_val.from_str(js_ctx, str_float_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_int(js_ctx, str_float_jval)
    assert (
        str(excinfo.value)
        == f'Expected JavaScript value to be a number: "{str_float_pyval}"'
    )
    actual = ultra.js_val.to_int(js_ctx, str_float_jval, strict=False)
    assert actual == int_pyval


def test_from_str__to_str(faker, js_ctx):
    # Scenario - string:
    str_pyval = faker.sentence()
    str_jval = ultra.js_val.from_str(js_ctx, str_pyval)
    actual = ultra.js_val.to_str(js_ctx, str_jval)
    assert actual == str_pyval

    # Scenario - null coercion:
    null_jval = ultra.js_val.from_none(js_ctx)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_str(js_ctx, null_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a string: null'
    actual = ultra.js_val.to_str(js_ctx, null_jval, strict=False)
    assert actual == 'null'

    # Scenario - bool coercion:
    bool_pyval = True
    bool_jval = ultra.js_val.from_bool(js_ctx, bool_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_str(js_ctx, bool_jval)
    assert str(excinfo.value) == 'Expected JavaScript value to be a string: true'
    actual = ultra.js_val.to_str(js_ctx, bool_jval, strict=False)
    assert actual == 'true'

    # Scenario - float coercion:
    float_pyval = 3.14
    float_jval = ultra.js_val.from_float(js_ctx, float_pyval)
    with pytest.raises(TypeError) as excinfo:
        ultra.js_val.to_str(js_ctx, float_jval)
    assert (
        str(excinfo.value) == f'Expected JavaScript value to be a string: {float_pyval}'
    )
    actual = ultra.js_val.to_str(js_ctx, float_jval, strict=False)
    assert actual == str(float_pyval)

    # Scenario - int coercion:
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
