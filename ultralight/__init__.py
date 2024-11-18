import _cffi_backend  # type: ignore
import logging
import pathlib
import platform
from ._cffi import ffi
from typing import TypeAlias

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
"""A default logger for the ``ultralight-cffi`` wrapper to log debug info to.

Adjust this as desired by setting the log level::

    >>> ultralight.logger.setLevel(logging.DEBUG)
"""


Lib: TypeAlias = _cffi_backend.Lib


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
    return libs[-1]


__all__ = [
    'ffi',
    'Lib',
    'load',
    'logger',
]
