from __future__ import annotations

import _cffi_backend
import cffi
import logging
import pathlib
import platform
import types
from . import _bindings
from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import Literal
from typing import TypeAlias
from typing import TypeVar
from typing import overload

ffi = _bindings.ffi

# Note: The library names are ordered according to the required initialization
# sequence; i.e. UltralightCore must be loaded before WebCore, etc.
_DARWIN_LIBRARY_NAMES = [
    'libUltralightCore.dylib',
    'libWebCore.dylib',
    'libUltralight.dylib',
    'libAppCore.dylib',
]
_LINUX_LIBRARY_NAMES = [
    'libUltralightCore.so',
    'libWebCore.so',
    'libUltralight.so',
    'libAppCore.so',
]
_WINDOWS_LIBRARY_NAMES = [
    'UltralightCore.dll',
    'WebCore.dll',
    'Ultralight.dll',
    'AppCore.dll',
]


logger = logging.getLogger(__name__)  # TODO: move elsewhere?
"""A default logger for the :mod:`ultralight_cffi` wrapper to log debug info to.

Adjust this as desired by setting the log level::

    >>> ultralight.logger.setLevel(logging.DEBUG)
"""


_T = TypeVar('_T')


class Pointer(Generic[_T]):  # TODO: move to `_ffi.py`
    if TYPE_CHECKING:

        @overload
        def __getitem__(self, key: int) -> _T: ...

        @overload
        def __getitem__(self, key: slice) -> Pointer[_T]: ...

        def __getitem__(self, key: int | slice) -> _T | Pointer[_T]: ...

        def __setitem__(self, key: int, value: _T) -> None: ...


if TYPE_CHECKING:  # CFFI type annotation workarounds

    NULL = Pointer[Any]()

    # FFI.CData is not available at runtime, so define an alias to be used for static
    # typing without causing a meltdown at runtime:
    CData: TypeAlias = cffi.FFI.CData
    CType: TypeAlias = cffi.FFI.CType

    # The official `types-cffi` stubs massacre the signatures of the decorated methods,
    # so these definitions serve as a partial replacement for more reliable static
    # typing, but with no runtime effect.

    @overload
    def cast(
        cdecl: Literal['struct OpaqueJSValue *'],
        source: CData | int,
    ) -> _stubs.JSValueRef: ...

    @overload
    def cast(
        cdecl: str | CType,
        source: CData | int,
    ) -> CData | _stubs.JSValueRef: ...

    def cast(
        cdecl: str | CType,
        source: CData | int,
    ) -> CData | _stubs.JSValueRef: ...

    def typeof(
        cdecl: (
            _stubs.JSValueRef
            | _stubs.JSObjectRef
            | str
            | CData
            | types.BuiltinFunctionType
            | types.FunctionType
        ),
    ) -> CType: ...

    @overload
    def new(
        cdecl: Literal['JSStringRef[]'],
        init: list[_stubs.JSStringRef | None],
    ) -> Pointer[_stubs.JSStringRef]: ...

    @overload
    def new(
        cdecl: Literal['JSValueRef[]'],
        init: list[_stubs.JSValueRef | None] | list[_stubs.JSValueRef],
    ) -> Pointer[_stubs.JSValueRef]: ...

    @overload
    def new(
        cdecl: Literal['JSValueRef *'],
        init: Any = ...,
    ) -> Pointer[_stubs.JSValueRef]: ...

    @overload
    def new(
        cdecl: Literal['ULString *'],
        init: Any = ...,
    ) -> Pointer[_stubs.ULString]: ...

    @overload
    def new(
        cdecl: str,
        init: Any = ...,
    ) -> (
        Pointer[_stubs.JSStringRef]
        | Pointer[_stubs.JSValueRef]
        | Pointer[_stubs.ULString]
        | CData
    ): ...

    def new(
        cdecl: str, init: Any = None
    ) -> (
        Pointer[_stubs.JSStringRef]
        | Pointer[_stubs.JSValueRef]
        | Pointer[_stubs.ULString]
        | CData
    ):
        """Equivalent to ``ffi.new(...)`` but with proper static typing, based on the
        ``cdecl`` argument.

        In most cases, the ``cdecl`` argument is a string literal, in which case the
        static typing can be inferred accordingly.
        """

    @overload
    def unpack(
        cdata: Pointer[_stubs.JSValueRef],
        length: int,
    ) -> list[_stubs.JSValueRef]: ...

    @overload
    def unpack(
        cdata: CData,
        length: int,
    ) -> bytes | str | list[Any]: ...

    def unpack(
        cdata: CData | Pointer[_stubs.JSValueRef],
        length: int,
    ) -> bytes | str | list[Any]:
        """Equivalent to ``ffi.unpack(...)`` but with proper static typing.

        See :meth:`new` for explanation.
        """

    def callback(
        cdecl: str | cffi.FFI.CType,
        *,
        error: Any = None,
        onerror: Callable[[Exception, Any, Any], None] | None = None,
    ) -> Callable[[_T], _T]:
        def wrap(func: _T) -> _T:
            return func

        return wrap

else:
    callback = ffi.callback
    CData = _cffi_backend._CDataBase  # pylint: disable=protected-access
    CType = _cffi_backend.CType
    new = ffi.new
    NULL = ffi.NULL
    typeof = ffi.typeof
    unpack = ffi.unpack


Lib: TypeAlias = _cffi_backend.Lib

_lib: Lib | None = None


def _get_library_names() -> list[str]:
    """Determine the shared library names based on the platform."""
    sys = platform.system()
    match sys:
        case 'Darwin':
            names = _DARWIN_LIBRARY_NAMES
        case 'Linux':
            names = _LINUX_LIBRARY_NAMES
        case 'Windows':
            names = _WINDOWS_LIBRARY_NAMES
        case _:
            raise RuntimeError(f'Unsupported platform: {sys}')
    return names


def _load_lib(
    library_name: str,
    library_path: pathlib.Path | None = None,
) -> Lib:
    """Loads a single Ultralight shared library file using FFI's ``dlopen`` wrapper."""
    if library_path is not None:
        library_name = str(library_path / library_name)
    logger.debug('Loading shared library: %s', library_name)
    return ffi.dlopen(library_name)


def load(
    library_path: pathlib.Path | str | None = None,
) -> Lib:
    """Loads the Ultralight shared libraries, and returns a combined FFI interface.

    Ultralight consists of multiple shared libraries.  This method loads all of them
    according to the required initialization ordering/sequence, and then returns a
    single, combined FFI interface that provides access to the full set of symbols.
    Although multiple ``dlopen`` calls are made, the runtime linker loads all the
    symbols into the process namespace, and the FFI interface doesn't care which shared
    library provides which individual symbols.

    Warning:
        The libraries are loaded using FFI's ``dlopen`` wrapper but no attempt is made
        to subsequently close the libraries with ``dlclose``. This could be improved
        in the future.
    """

    if isinstance(library_path, str):
        library_path = pathlib.Path(library_path)

    # Note: Slightly kludgy to retain only the last library object, but this has the
    # benefit of providing a single, consolidated interface, rather than making
    # separate FFI bindings for each shared library.
    library_names = _get_library_names()
    libs = [_load_lib(library_name, library_path) for library_name in library_names]

    global _lib  # FIXME/TMP  # pylint: disable=global-statement
    _lib = libs[-1]

    return _lib


def get_lib() -> Lib:
    """Ensures that the Ultralight shared libraries have been loaded, and returns the
    FFI interface.

    Raises:
        :class:`RuntimeError`: If the shared libraries haven't been loaded via
        :meth:`load`.
    """
    if _lib is None:
        raise RuntimeError(
            'Ultralight shared libraries have not been loaded yet.  `ultralight.load` '
            'needs to be called beforehand.'
        )
    return _lib


from . import _stubs  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'callback',
    'ffi',
    'get_lib',
    'logger',
    'new',
    'new',
    'NULL',
    'unpack',
    'unpack',
]
