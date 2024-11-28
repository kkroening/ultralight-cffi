from .. import _stubs
from . import js_error
from . import js_str


def to_str(
    ctx: _stubs.JSContextRef,
    jval: _stubs.JSValueRef,
    indent: int = 0,
) -> str:
    with js_error.scoped(ctx) as error_jval_ref:  # Warning: potentially recursive
        jstr = _stubs.JSValueCreateJSONString(
            ctx,
            jval,
            indent,
            error_jval_ref,
        )
    return js_str.decode(jstr)
