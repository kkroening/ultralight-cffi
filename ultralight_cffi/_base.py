from __future__ import annotations

import _cffi_backend
import logging
import pathlib
import platform
from ._bindings import ffi
from cffi import FFI
from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TypeAlias
from typing import TypeVar
from typing import overload

_T = TypeVar('_T')


class Pointer(Generic[_T]):
    if TYPE_CHECKING:

        @overload
        def __getitem__(self, key: int) -> _T: ...

        @overload
        def __getitem__(self, key: slice) -> Pointer[_T]: ...

        def __getitem__(self, key: int | slice) -> _T | Pointer[_T]: ...

        def __setitem__(self, key: int, value: _T) -> None: ...


if TYPE_CHECKING:
    NULL = Pointer[Any]()
else:
    NULL = ffi.NULL


if TYPE_CHECKING:  # CFFI type annotation workarounds

    # The official `types-cffi` stubs massacre the signature of the decorated method,
    # so this signature serves as a replacement for more reliable static typing, but
    # with no runtime effect.

    def callback(
        cdecl: str | FFI.CType,
        *,
        error: Any = None,
        onerror: Callable[[Exception, Any, Any], None] | None = None,
    ) -> Callable[[_T], _T]:
        def wrap(func: _T) -> _T:
            return func

        return wrap

    # FFI.CData is not available at runtime, so define an alias to be used for static
    # typing without causing a meltdown at runtime.

    CData: TypeAlias = FFI.CData
else:
    callback = ffi.callback
    CData: TypeAlias = Any


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


logger = logging.getLogger(__name__)
"""A default logger for the :mod:`ultralight_cffi` wrapper to log debug info to.

Adjust this as desired by setting the log level::

    >>> ultralight.logger.setLevel(logging.DEBUG)
"""


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
