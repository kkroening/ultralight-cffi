from . import _base
from . import _bindings
from . import _stubs
from ._base import Pointer
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import overload

if TYPE_CHECKING:

    @overload
    def new(
        cdecl: Literal['JSStringRef[]'],
        init: list[_stubs.JSStringRef | None],
    ) -> Pointer[_stubs.JSStringRef]: ...
    @overload
    def new(
        cdecl: Literal['JSValueRef[]'],
        init: list[_stubs.JSValueRef | None],
    ) -> Pointer[_stubs.JSValueRef]: ...
    @overload
    def new(
        cdecl: str,
        init: Any = ...,
    ) -> Any: ...

    def new(cdecl: str, init: Any = None) -> Any:
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
        cdata: _base.CData,
        length: int,
    ) -> bytes | str | list[Any]: ...

    def unpack(
        cdata: _base.CData | Pointer[_stubs.JSValueRef],
        length: int,
    ) -> bytes | str | list[Any]:
        """Equivalent to ``ffi.unpack(...)`` but with proper static typing.

        See :meth:`new` for explanation.
        """

else:
    new = _bindings.ffi.new
    unpack = _bindings.ffi.unpack

__all__ = [
    'new',
    'unpack',
]
