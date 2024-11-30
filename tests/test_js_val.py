import json
import math
import pytest
import ultralight_cffi as ultra


class Test_JSValue__to_json_str__from_json_str:
    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        # Note: NULL pointers are distinct from null JS values.  `JSValue.from_none`
        # avoids ever creating NULL pointers though because it creates unnecessary,
        # redundant situations.  In the majority of situations, NULL pointers should be
        # avoided; but if absolutely necessary, `ultra.NULL` can be used (rather than
        # `JSValue.from_none`).
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        assert ultra.JSValueIsNull(js_ctx, jval.ref) is True
        assert ultra.JSValueIsUndefined(js_ctx, jval.ref) is False
        actual = jval.to_json_str()
        assert actual == 'null'

    def test__undefined(self, js_ctx):
        jval = ultra.JSValue.from_none(js_ctx, undefined=True)
        assert ultra.JSValueIsNull(js_ctx, jval.ref) is False
        assert ultra.JSValueIsUndefined(js_ctx, jval.ref) is True
        actual = jval.to_json_str()
        assert actual is None

    def test__bool(self, js_ctx):
        jval = ultra.JSValue.from_bool(js_ctx, True)
        actual = jval.to_json_str()
        assert actual == 'true'

    def test__float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)  # low precision avoids JSON rounding discrepancies
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        actual = jval.to_json_str()
        assert actual == str(pyval)

    def test__nan(self, js_ctx):
        # Note: Dumping NaN in JS (e.g. via `JSON.stringify(NaN)`) gives `"null"` - in
        # contrast to Python's `json.dumps(float('nan'))` which gives `"NaN"`.
        pyval = float('nan')
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        assert ultra.JSValueIsNumber(js_ctx, jval.ref) is True
        actual = jval.to_json_str()
        assert actual == 'null'

    def test__int(self, faker, js_ctx):
        pyval = faker.pyint()
        jval = ultra.JSValue.from_int(js_ctx, pyval)
        actual = jval.to_json_str()
        assert actual == str(pyval)

    def test__str(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        actual = jval.to_json_str()
        assert actual == json.dumps(pyval)


class Test_JSValue__from_none__to_none:
    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        actual = jval.to_none()
        assert actual is None

    def test__undefined(self, js_ctx):
        jval = ultra.JSValue.from_none(js_ctx, undefined=True)
        actual = jval.to_none()
        assert actual is None

    def test__bool(self, faker, js_ctx):
        jval = ultra.JSValue.from_bool(js_ctx, False)
        with pytest.raises(TypeError) as excinfo:
            jval.to_none()
        assert (
            str(excinfo.value)
            == 'Expected JavaScript value to be null or undefined: false'
        )

    def test__float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_none()
        assert (
            str(excinfo.value)
            == f'Expected JavaScript value to be null or undefined: {pyval}'
        )

    def test__str(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_none()
        assert (
            str(excinfo.value)
            == f'Expected JavaScript value to be null or undefined: {json.dumps(pyval)}'
        )


class Test_JSValue__from_bool__to_bool:
    def test__false(self, js_ctx):
        jval = ultra.JSValue.from_bool(js_ctx, False)
        actual = jval.to_bool()
        assert actual is False

    def test__true(self, js_ctx):
        jval = ultra.JSValue.from_bool(js_ctx, True)
        actual = jval.to_bool()
        assert actual is True

    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        with pytest.raises(TypeError) as excinfo:
            jval.to_bool()
        assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: null'

        actual = jval.to_bool(strict=False)
        assert actual is False

    def test__undefined(self, js_ctx):
        jval = ultra.JSValue.from_none(js_ctx, undefined=True)
        assert ultra.JSValueIsUndefined(js_ctx, jval.ref) is True
        with pytest.raises(TypeError) as excinfo:
            jval.to_bool()
        assert (
            str(excinfo.value) == 'Expected JavaScript value to be a boolean: undefined'
        )

        actual = jval.to_bool(strict=False)
        assert actual is False

    def test__falsy_number(self, js_ctx):
        pyval = 0
        jval = ultra.JSValue.from_int(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            actual = jval.to_bool()
        assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: 0'

        actual = jval.to_bool(strict=False)
        assert actual is False

    def test__truthy_number(self, faker, js_ctx):
        pyval = faker.pyint(1, 100)
        jval = ultra.JSValue.from_int(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            actual = jval.to_bool()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a boolean: {pyval}'
        )

        actual = jval.to_bool(strict=False)
        assert actual is True

    def test__nan(self, js_ctx):
        pyval = float('nan')
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_bool()
        assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: null'

        actual = jval.to_bool(strict=False)
        assert actual is False

    def test__falsy_string(self, js_ctx):
        jval = ultra.JSValue.from_str(js_ctx, '')
        with pytest.raises(TypeError) as excinfo:
            jval.to_bool()
        assert str(excinfo.value) == 'Expected JavaScript value to be a boolean: ""'

        actual = jval.to_bool(strict=False)
        assert actual is False

    def test__false_string(self, js_ctx):
        # Similar to the other truthy/falsy string coercion scenarios, but with the
        # text `"false"` to confirm that the JS runtime does not try to parse the text
        # as a boolean (i.e. behaving just like Python, where `bool('False')` is True).
        jval = ultra.JSValue.from_str(js_ctx, 'false')
        with pytest.raises(TypeError) as excinfo:
            jval.to_bool()
        assert (
            str(excinfo.value) == 'Expected JavaScript value to be a boolean: "false"'
        )

        actual = jval.to_bool(strict=False)
        assert actual is True

    def test__truthy_string(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_bool()
        assert (
            str(excinfo.value)
            == f'Expected JavaScript value to be a boolean: "{pyval}"'
        )

        actual = jval.to_bool(strict=False)
        assert actual is True


class Test_JSValue__from_float__to_float:
    def test__float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        actual = jval.to_float()
        assert actual == pyval

    def test__nan(self, js_ctx):
        pyval = float('nan')
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        actual = jval.to_float()
        assert math.isnan(actual)

    @pytest.mark.parametrize('negative', [False, True])
    def test__infinity(self, js_ctx, negative):
        pyval = float('-inf' if negative else 'inf')
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        actual = jval.to_float()
        assert actual == pyval

    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        with pytest.raises(TypeError) as excinfo:
            jval.to_float()
        assert str(excinfo.value) == 'Expected JavaScript value to be a number: null'

        actual = jval.to_float(strict=False)
        assert actual == 0.0

    def test__bool(self, js_ctx):
        pyval = True
        jval = ultra.JSValue.from_bool(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_float()
        assert str(excinfo.value) == 'Expected JavaScript value to be a number: true'

        actual = jval.to_float(strict=False)
        assert actual == float(pyval)

    def test__string_empty(self, js_ctx):
        pyval = ''
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_float()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a number: "{pyval}"'
        )

        actual = jval.to_float(strict=False)
        assert actual == 0.0

    def test__string_non_numeric(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_float()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a number: "{pyval}"'
        )

        actual = jval.to_float(strict=False)
        assert math.isnan(actual)

    def test__stringified_float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_str(js_ctx, str(pyval))
        actual = jval.to_float(strict=False)
        assert actual == pyval

    def test__stringified_nan(self, js_ctx):
        jval = ultra.JSValue.from_str(js_ctx, 'nan')
        actual = jval.to_float(strict=False)
        assert math.isnan(actual)

    @pytest.mark.parametrize('negative', [False, True])
    def test__stringified_infinity(self, js_ctx, negative):
        pyval = float('-inf' if negative else 'inf')
        jval = ultra.JSValue.from_str(js_ctx, '-Infinity' if negative else 'Infinity')
        actual = jval.to_float(strict=False)
        assert not math.isnan(actual)
        assert not math.isfinite(actual)
        assert actual == pyval


class Test_JSValue__from_int__to_int:
    def test__int(self, faker, js_ctx):
        pyval = faker.pyint(1, 1000)
        jval = ultra.JSValue.from_int(js_ctx, pyval)
        actual = jval.to_int()
        assert actual == pyval

    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        with pytest.raises(TypeError) as excinfo:
            jval.to_int()
        assert str(excinfo.value) == 'Expected JavaScript value to be a number: null'

        actual = jval.to_int(strict=False)
        assert actual == 0

    def test__bool(self, js_ctx):
        pyval = True
        jval = ultra.JSValue.from_bool(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_int()
        assert str(excinfo.value) == 'Expected JavaScript value to be a number: true'

        actual = jval.to_int(strict=False)
        assert actual == int(pyval)

    def test__float(self, faker, js_ctx):
        pyval = (
            faker.pyint(-100, 100) + 0.8
        )  # >0.5 offset to confirm truncation rather than rounding
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        actual = jval.to_int()
        assert actual == int(pyval)

    @pytest.mark.parametrize(
        'pyval',
        [
            'false',
            'nan',
            'null',
            'sample str',
            'true',
        ],
    )
    def test__string_non_numeric(self, js_ctx, pyval):
        jval = ultra.JSValue.from_str(js_ctx, pyval)

        with pytest.raises(TypeError) as excinfo:
            jval.to_int()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a number: "{pyval}"'
        )

        with pytest.raises(ValueError) as excinfo:
            jval.to_int(strict=False)
        assert str(excinfo.value) == f'Cannot convert NaN to int: "{pyval}"'

    @pytest.mark.parametrize('negative', [False, True])
    def test__stringified_infinity(self, js_ctx, negative):
        pyval = '-Infinity' if negative else 'Infinity'
        jval = ultra.JSValue.from_str(js_ctx, pyval)

        with pytest.raises(TypeError) as excinfo:
            jval.to_int()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a number: "{pyval}"'
        )

        with pytest.raises(ValueError) as excinfo:
            jval.to_int(strict=False)
        assert str(excinfo.value) == f'Cannot convert infinite number to int: "{pyval}"'

    def test__stringified_float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_str(js_ctx, str(pyval))
        with pytest.raises(TypeError) as excinfo:
            jval.to_int()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a number: "{pyval}"'
        )

        actual = jval.to_int(strict=False)
        assert actual == int(pyval)


class Test_JSValue__from_str__to_str:
    def test__str(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        actual = jval.to_str()
        assert actual == pyval

    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        with pytest.raises(TypeError) as excinfo:
            jval.to_str()
        assert str(excinfo.value) == 'Expected JavaScript value to be a string: null'
        actual = jval.to_str(strict=False)
        assert actual == 'null'

    def test__undefined(self, js_ctx):
        jval = ultra.JSValue.from_none(js_ctx, undefined=True)
        with pytest.raises(TypeError) as excinfo:
            jval.to_str()
        assert (
            str(excinfo.value) == 'Expected JavaScript value to be a string: undefined'
        )

        actual = jval.to_str(strict=False)
        assert actual == 'undefined'

    def test__bool(self, js_ctx):
        pyval = True
        jval = ultra.JSValue.from_bool(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_str()
        assert str(excinfo.value) == 'Expected JavaScript value to be a string: true'

        actual = jval.to_str(strict=False)
        assert actual == 'true'

    def test__float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_str()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a string: {pyval}'
        )

        actual = jval.to_str(strict=False)
        assert actual == str(pyval)

    def test__int(self, faker, js_ctx):
        pyval = faker.pyint()
        jval = ultra.JSValue.from_int(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_str()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be a string: {pyval}'
        )

        actual = jval.to_str(strict=False)
        assert actual == str(pyval)


class Test_JSValue__from_dict__to_dict:
    def test__dict(self, faker, js_ctx):
        pydict1 = {'sample_key': faker.lexify('sample_???')}
        jval1 = ultra.JSValue.from_dict(js_ctx, pydict1)
        actual = jval1.to_dict()
        assert actual == pydict1

        pydict2 = {'nested_key': pydict1, 'unnested_key': faker.pyint()}
        jval2 = ultra.JSValue.from_dict(js_ctx, pydict2)
        actual = jval2.to_dict()
        assert actual == pydict2

    @pytest.mark.parametrize('with_null_pointer', [False, True])
    def test__null(self, js_ctx, with_null_pointer):
        jval = (
            ultra.JSValue(ultra.NULL, js_ctx)
            if with_null_pointer
            else ultra.JSValue.from_none(js_ctx)
        )
        with pytest.raises(TypeError) as excinfo:
            jval.to_dict()
        assert str(excinfo.value) == 'Expected JavaScript value to be an object: null'

    def test__undefined(self, js_ctx):
        jval = ultra.JSValue.from_none(js_ctx, undefined=True)
        with pytest.raises(TypeError) as excinfo:
            jval.to_dict()
        assert (
            str(excinfo.value) == 'Expected JavaScript value to be an object: undefined'
        )

    def test__bool(self, js_ctx):
        pyval = True
        jval = ultra.JSValue.from_bool(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_dict()
        assert str(excinfo.value) == 'Expected JavaScript value to be an object: true'

    def test__float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_float(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_dict()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be an object: {pyval}'
        )

    def test__int(self, faker, js_ctx):
        pyval = faker.pyint()
        jval = ultra.JSValue.from_int(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_dict()
        assert (
            str(excinfo.value) == f'Expected JavaScript value to be an object: {pyval}'
        )

    def test__str(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_str(js_ctx, pyval)
        with pytest.raises(TypeError) as excinfo:
            jval.to_dict()
        assert (
            str(excinfo.value)
            == f'Expected JavaScript value to be an object: "{pyval}"'
        )


class Test_JSValue__from_python__to_python:
    @pytest.mark.parametrize('prefer_undefined', [False, True])
    def test__none(self, js_ctx, prefer_undefined):
        jval = ultra.JSValue.from_python(
            js_ctx, None, prefer_undefined=prefer_undefined
        )
        assert jval.to_python() is None

    def test__bool(self, faker, js_ctx):
        pyval = faker.pybool()
        jval = ultra.JSValue.from_python(js_ctx, pyval)
        assert jval.to_python() is pyval

    def test__float(self, faker, js_ctx):
        pyval = faker.pyfloat(3, 3)
        jval = ultra.JSValue.from_python(js_ctx, pyval)
        assert jval.to_python(prefer_float=True) == pyval

    def test__int(self, faker, js_ctx):
        pyval = faker.pyint()
        jval = ultra.JSValue.from_python(js_ctx, pyval)
        assert jval.to_python() == pyval

    def test__str(self, faker, js_ctx):
        pyval = faker.sentence()
        jval = ultra.JSValue.from_python(js_ctx, pyval)
        assert jval.to_python() == pyval

    def test__dict(self, faker, js_ctx):
        pyval = {'key1a': 'value1a', 'key1b': {'key2a': 'value2a'}}
        jval = ultra.JSValue.from_python(js_ctx, pyval)
        assert jval.to_python() == pyval


def test_JSValue__scoped(faker, js_ctx):
    def get_protected_count():
        stats = ultra.JSValue(
            ultra.JSGetMemoryUsageStatistics(js_ctx), js_ctx
        ).to_python()
        return stats['protectedObjectCount']

    orig_protected_count = get_protected_count()

    pyval1 = faker.sentence()
    pyval2 = faker.sentence()

    with ultra.JSValue.scoped_from(js_ctx, pyval1) as jval1:
        assert jval1.to_python() == pyval1
        assert get_protected_count() == orig_protected_count + 1

        # Expectation - re-protecting doesn't increase/decrease protection count:
        with jval1.scoped() as jval2:
            assert jval2 is jval1
            assert get_protected_count() == orig_protected_count + 1
        assert get_protected_count() == orig_protected_count + 1

        # Expectation - nesting scope for different value has independent protection:
        with ultra.JSValue.scoped_from(js_ctx, pyval2) as jval2:
            assert jval2.to_python() == pyval2
            assert get_protected_count() == orig_protected_count + 2
        assert get_protected_count() == orig_protected_count + 1

    # Expectation - protection evaporates when context has exited:
    assert get_protected_count() == orig_protected_count
