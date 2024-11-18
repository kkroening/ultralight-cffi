import abc
import inspect
from . import _base
from ._base import CData
from ._bindings import ffi
from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Self
from typing import TypeAlias
from typing import cast
from typing_extensions import Buffer

# TODO: ideally generate these supplemental annotations automatically; written by hand
# for now.

if TYPE_CHECKING:
    ULSurfaceDefinitionCreateCallback: TypeAlias = Callable[[int, int], CData]
    ULSurfaceDefinitionDestroyCallback: TypeAlias = Callable[[CData], None]
    ULSurfaceDefinitionGetWidthCallback: TypeAlias = Callable[[CData], int]
    ULSurfaceDefinitionGetHeightCallback: TypeAlias = Callable[[CData], int]
    ULSurfaceDefinitionGetRowBytesCallback: TypeAlias = Callable[[CData], int]
    ULSurfaceDefinitionGetSizeCallback: TypeAlias = Callable[[CData], int]
    ULSurfaceDefinitionLockPixelsCallback: TypeAlias = Callable[[CData], CData]
    ULSurfaceDefinitionUnlockPixelsCallback: TypeAlias = Callable[[CData], None]
    ULSurfaceDefinitionResizeCallback: TypeAlias = Callable[[CData, int, int], None]

    class ULSurfaceDefinition:
        create: ULSurfaceDefinitionCreateCallback
        destroy: ULSurfaceDefinitionDestroyCallback
        get_width: ULSurfaceDefinitionGetWidthCallback
        get_height: ULSurfaceDefinitionGetHeightCallback
        get_row_bytes: ULSurfaceDefinitionGetRowBytesCallback
        get_size: ULSurfaceDefinitionGetSizeCallback
        lock_pixels: ULSurfaceDefinitionLockPixelsCallback
        unlock_pixels: ULSurfaceDefinitionUnlockPixelsCallback
        resize: ULSurfaceDefinitionResizeCallback

else:
    ULSurfaceDefinitionCreateCallback: TypeAlias = Any
    ULSurfaceDefinitionDestroyCallback: TypeAlias = Any
    ULSurfaceDefinitionGetWidthCallback: TypeAlias = Any
    ULSurfaceDefinitionGetHeightCallback: TypeAlias = Any
    ULSurfaceDefinitionGetRowBytesCallback: TypeAlias = Any
    ULSurfaceDefinitionGetSizeCallback: TypeAlias = Any
    ULSurfaceDefinitionLockPixelsCallback: TypeAlias = Any
    ULSurfaceDefinitionUnlockPixelsCallback: TypeAlias = Any
    ULSurfaceDefinitionResizeCallback: TypeAlias = Any

    ULSurfaceDefinition: TypeAlias = Any

CustomSurfaceHandle: TypeAlias = CData


class CustomSurface(abc.ABC):
    """Python-level abstraction for Pythonically defining user-defined, custom surface
    implementations using ordinary Python (data)classes.
    """

    _cb__create: ClassVar[ULSurfaceDefinitionCreateCallback | None] = None
    """A subclass-specific reference to the creation callback.

    Unlike the other custom surface callbacks that have only a single definition (e.g.
    :meth:`._cb__lock_pixels`) that dispatches to the appropriate Python subclass, the
    creation callback is special because each concrete subclass of
    :class:`CustomSurface` needs its own creation callback that knows how to instantiate
    that particular subclass - hence why this is a class variable rather than a class
    method.  See :meth:`_generate_cb__create`.
    """

    _handle: CustomSurfaceHandle

    def __init__(self) -> None:
        self._handle = ffi.new_handle(self)

    @classmethod
    def from_user_data(cls, user_data: CData) -> Self:
        obj = ffi.from_handle(user_data)
        if not isinstance(obj, cls):
            raise TypeError(
                f'Expected FFI handle to point to {cls.__qualname__} instance; got {obj}'
            )
        return obj

    @classmethod
    def from_ffi(
        cls,
        lib: _base.Lib,  # FIXME: use context instead
        ul_surface: Any,
    ) -> Self:
        user_data = lib.ulSurfaceGetUserData(ul_surface)  # type: ignore[attr-defined]
        return cls.from_user_data(user_data)

    @classmethod
    @abc.abstractmethod
    def create(cls, width: int, height: int) -> Self:
        raise NotImplementedError()

    @abc.abstractmethod
    def destroy(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_width(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_height(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_size(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_row_bytes(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def lock_pixels(self) -> Buffer:
        raise NotImplementedError()

    @abc.abstractmethod
    def unlock_pixels(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def resize(self, width: int, height: int) -> None:
        raise NotImplementedError()

    @staticmethod
    @_base.callback('void(void*)')
    def _cb__destroy(user_data: CData) -> None:
        surface = ffi.from_handle(user_data)
        surface.destroy()
        del surface

    @staticmethod
    @_base.callback('unsigned int(void*)')
    def _cb__get_width(user_data: CData) -> int:
        surface: CustomSurface = ffi.from_handle(user_data)
        return surface.get_width()

    @staticmethod
    @_base.callback('unsigned int(void*)')
    def _cb__get_height(user_data: CData) -> int:
        surface: CustomSurface = ffi.from_handle(user_data)
        return surface.get_height()

    @staticmethod
    @_base.callback('unsigned int(void*)')
    def _cb__get_row_bytes(user_data: CData) -> int:
        surface: CustomSurface = ffi.from_handle(user_data)
        return surface.get_row_bytes()

    @staticmethod
    @_base.callback('size_t(void*)')
    def _cb__get_size(user_data: CData) -> int:
        surface: CustomSurface = ffi.from_handle(user_data)
        return surface.get_size()

    @staticmethod
    @_base.callback('void*(void*)')
    def _cb__lock_pixels(user_data: CData) -> Any:
        surface: CustomSurface = ffi.from_handle(user_data)
        return ffi.from_buffer(surface.lock_pixels())

    @staticmethod
    @_base.callback('void(void*)')
    def _cb__unlock_pixels(user_data: CData) -> None:
        surface: CustomSurface = ffi.from_handle(user_data)
        surface.unlock_pixels()

    @staticmethod
    @_base.callback('void(void*, unsigned int, unsigned int)')
    def _cb__resize(user_data: CData, width: int, height: int) -> None:
        surface: CustomSurface = ffi.from_handle(user_data)
        return surface.resize(width, height)

    @classmethod
    def _generate_cb__create(cls) -> ULSurfaceDefinitionCreateCallback:
        """Dynamically generates a creation callback for the class.

        The other callbacks can all be singletons since they dispatch to the appropriate
        subclass by the ``user_data`` handle / ``self`` reference, but creation is
        trickier because there's no ``self`` when it's called, and the callback needs to
        remember which subclass it needs to instantiate.  Basically, there should be
        exactly one instance of the callback function per concrete subclass/
        implementation of :class:`CustomSurface`, and the reference needs to be held as
        a class variable in order to prevent premature garbage collection.
        """

        @_base.callback('void*(unsigned int, unsigned int)')
        def _cb__create(width: int, height: int) -> CData:
            surface = cls.create(width, height)
            return surface._handle  # pylint: disable=protected-access

        return _cb__create

    @classmethod
    def get_definition(cls) -> ULSurfaceDefinition:
        defn: ULSurfaceDefinition = cast(
            ULSurfaceDefinition, ffi.new('ULSurfaceDefinition*')
        )
        if inspect.isabstract(cls):
            raise TypeError(
                f'Unable to generate ULSurfaceDefinition for abstract {cls}'
            )

        # Generate a per-subclass `_cb__create` ffi callback, while avoiding
        # accidentally inheriting the super class' `_cb__create`.  (FIXME: find a less
        # tricky/clever way to do this)
        if cls._cb__create is None or (
            cls._cb__create is super()._cb__create  # type: ignore[misc] # pylint: disable=no-member
        ):
            cls._cb__create = cls._generate_cb__create()

        assert cls._cb__create is not None
        defn.create = cls._cb__create
        defn.destroy = cls._cb__destroy
        defn.get_width = cls._cb__get_width
        defn.get_height = cls._cb__get_height
        defn.get_row_bytes = cls._cb__get_row_bytes
        defn.get_size = cls._cb__get_size
        defn.lock_pixels = cls._cb__lock_pixels
        defn.unlock_pixels = cls._cb__unlock_pixels
        defn.resize = cls._cb__resize
        return defn
