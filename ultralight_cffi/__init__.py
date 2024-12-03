from . import _stubs
from . import glue
from ._bindings import ffi
from ._ffi import NULL
from ._ffi import CData
from ._ffi import Lib
from ._ffi import Pointer
from ._ffi import callback
from ._ffi import load
from ._ffi import logger
from ._ffi import new
from ._ffi import typeof
from ._ffi import unpack
from ._surface import CustomSurface
from .glue import JSContext
from .glue import JSFunction
from .glue import JSGlobalContext
from .glue import JSObject
from .glue import JSValue
from .glue import UltralightError
from .glue import UltralightJSError
from .glue import UltralightULError
from .glue import js_error
from .glue import js_str
from .glue import ul_error
from .glue import ul_str

# Note: wildcard imports generally suck, but since `_stubs.py` is auto-generated, this
# errs on the side of avoiding excessively redundant boilerplate.  The glue-layer
# submodules are gathered here but can also be explicitly imported as
# `ultralight_cffi.glue` to keep it all together.
from ._stubs import *  # isort: skip

__all__ = _stubs.__all__ + [
    'callback',
    'CData',
    'CustomSurface',
    'ffi',
    'glue',
    'JSContext',
    'JSFunction',
    'JSGlobalContext',
    'JSObject',
    'JSValue',
    'js_error',
    'js_str',
    'Lib',
    'load',
    'logger',
    'new',
    'NULL',
    'Pointer',
    'typeof',
    'UltralightError',
    'UltralightJSError',
    'UltralightULError',
    'ul_error',
    'ul_str',
    'unpack',
]
