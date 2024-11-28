from .. import _stubs
from . import _js_error
from . import _jstr


def jval_to_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    indent: int = 0,
) -> str:
    with _js_error.handle_js_error(
        ctx
    ) as error_jval_ref:  # Warning: potentially recursive
        jstr = _stubs.JSValueCreateJSONString(
            ctx,
            jval,
            indent,
            error_jval_ref,
        )
    return _jstr.jstr_decode(jstr)
