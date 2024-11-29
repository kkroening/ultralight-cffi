import pytest
import ultralight_cffi as ultra


def test__encode__decode__scoped(faker, js_ctx):
    pystr = faker.sentence()
    with ultra.js_str.scoped(pystr) as jstr1:
        assert ultra.js_str.decode(jstr1) == pystr

        # Nested scope should increase reference count while pointing to the same
        # underlying string:
        with ultra.js_str.scoped(jstr1) as jstr2:
            assert jstr1 == jstr2

    with pytest.raises(ValueError) as excinfo:
        ultra.js_str.decode(ultra.NULL)
    assert (
        str(excinfo.value)
        == 'Encountered null pointer while expecting a JavaScript string'
    )

    jstr = ultra.js_str.decode(ultra.NULL, strict=False)
    assert jstr == ''
