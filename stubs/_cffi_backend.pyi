import types
from _typeshed import Incomplete
from collections.abc import Callable
from typing import Any
from typing import ClassVar
from typing import TypeVar
from typing import overload

_T = TypeVar('_T')

ffi: Incomplete

FFI_CDECL: int
FFI_DEFAULT_ABI: int
RTLD_GLOBAL: int
RTLD_LAZY: int
RTLD_LOCAL: int
RTLD_NODELETE: int
RTLD_NOLOAD: int
RTLD_NOW: int
__version__: str

class CField:
    bitshift: Incomplete
    bitsize: Incomplete
    flags: Incomplete
    offset: Incomplete
    type: Incomplete

class CLibrary:
    def close_lib(self, *args: Any, **kwargs: Any) -> Any: ...
    def load_function(self, *args: Any, **kwargs: Any) -> Any: ...
    def read_variable(self, *args: Any, **kwargs: Any) -> Any: ...
    def write_variable(self, *args: Any, **kwargs: Any) -> Any: ...

class CType:
    abi: Incomplete
    args: Incomplete
    cname: Incomplete
    elements: Incomplete
    ellipsis: Incomplete
    fields: Incomplete
    item: Incomplete
    kind: Incomplete
    length: Incomplete
    relements: Incomplete
    result: Incomplete
    def __dir__(self) -> Any: ...

class FFI:
    class CData:
        def __add__(self, other: Any) -> Any: ...
        def __bool__(self) -> bool: ...
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
        def __complex__(self) -> complex: ...
        def __delattr__(self, name: Any) -> Any: ...
        def __delitem__(self, other: Any) -> None: ...
        def __dir__(self) -> Any: ...
        def __enter__(self) -> Any: ...
        def __eq__(self, other: object) -> bool: ...
        def __exit__(
            self,
            type: type[BaseException] | None,
            value: BaseException | None,
            traceback: types.TracebackType | None,
        ) -> Any: ...
        def __float__(self) -> float: ...
        def __ge__(self, other: object) -> bool: ...
        def __getitem__(self, index: Any) -> Any: ...
        def __gt__(self, other: object) -> bool: ...
        def __hash__(self) -> int: ...
        def __int__(self) -> int: ...
        def __iter__(self) -> Any: ...
        def __le__(self, other: object) -> bool: ...
        def __len__(self) -> int: ...
        def __lt__(self, other: object) -> bool: ...
        def __ne__(self, other: object) -> bool: ...
        def __radd__(self, other: Any) -> Any: ...
        def __rsub__(self, other: Any) -> Any: ...
        def __setattr__(self, name: Any, value: Any) -> Any: ...
        def __setitem__(self, index: Any, object: Any) -> None: ...
        def __sub__(self, other: Any) -> Any: ...

    class CType:
        abi: Incomplete
        args: Incomplete
        cname: Incomplete
        elements: Incomplete
        ellipsis: Incomplete
        fields: Incomplete
        item: Incomplete
        kind: Incomplete
        length: Incomplete
        relements: Incomplete
        result: Incomplete
        def __dir__(self) -> Any: ...

    class buffer:
        @classmethod
        def __init__(cls, *args: Any, **kwargs: Any) -> None: ...
        def __delitem__(self, other: Any) -> None: ...
        def __eq__(self, other: object) -> bool: ...
        def __ge__(self, other: object) -> bool: ...
        def __getitem__(self, index: Any) -> Any: ...
        def __gt__(self, other: object) -> bool: ...
        def __le__(self, other: object) -> bool: ...
        def __len__(self) -> int: ...
        def __lt__(self, other: object) -> bool: ...
        def __ne__(self, other: object) -> bool: ...
        def __setitem__(self, index: Any, object: Any) -> None: ...

    NULL: ClassVar[_CDataBase] = ...
    RTLD_GLOBAL: ClassVar[int] = ...
    RTLD_LAZY: ClassVar[int] = ...
    RTLD_LOCAL: ClassVar[int] = ...
    RTLD_NODELETE: ClassVar[int] = ...
    RTLD_NOLOAD: ClassVar[int] = ...
    RTLD_NOW: ClassVar[int] = ...
    error: ClassVar[type[ffi.error]] = ...
    errno: Incomplete
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def addressof(self, *args: Any, **kwargs: Any) -> Any: ...
    def alignof(self, *args: Any, **kwargs: Any) -> Any: ...
    def callback(self, *args: Any, **kwargs: Any) -> Callable[[_T], _T]: ...
    def cast(self, *args: Any, **kwargs: Any) -> Any: ...
    def def_extern(self, *args: Any, **kwargs: Any) -> Any: ...
    def dlclose(self, *args: Any, **kwargs: Any) -> Any: ...
    def dlopen(self, libpath: str, flags: int = ...) -> Lib: ...
    def from_buffer(self, *args: Any, **kwargs: Any) -> Any: ...
    def from_handle(self, *args: Any, **kwargs: Any) -> Any: ...
    def gc(self, *args: Any, **kwargs: Any) -> Any: ...
    def getctype(self, *args: Any, **kwargs: Any) -> Any: ...
    @overload
    def init_once(self, function: Any, tag: Any) -> Any: ...
    @overload
    def init_once(self) -> Any: ...
    def integer_const(self, *args: Any, **kwargs: Any) -> Any: ...
    def list_types(self, *args: Any, **kwargs: Any) -> Any: ...
    @overload
    def memmove(self, dest: Any, src: Any, n: Any) -> Any: ...
    @overload
    def memmove(self) -> Any: ...
    def new(self, *args: Any, **kwargs: Any) -> Any: ...
    def new_allocator(self, *args: Any, **kwargs: Any) -> Any: ...
    def new_handle(self, python_object: object) -> Any: ...
    def offsetof(self, *args: Any, **kwargs: Any) -> Any: ...
    def release(self, *args: Any, **kwargs: Any) -> Any: ...
    def sizeof(self, *args: Any, **kwargs: Any) -> Any: ...
    def string(self, orunicodestring: Any) -> Any: ...
    def typeof(self, *args: Any, **kwargs: Any) -> Any: ...
    def unpack(self, *args: Any, **kwargs: Any) -> Any: ...

class Lib:
    def __delattr__(self, name: Any) -> Any: ...
    def __dir__(self) -> Any: ...
    def __setattr__(self, name: Any, value: Any) -> Any: ...

class _CDataBase:
    def __add__(self, other: Any) -> Any: ...
    def __bool__(self) -> bool: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    def __complex__(self) -> complex: ...
    def __delattr__(self, name: Any) -> Any: ...
    def __delitem__(self, other: Any) -> None: ...
    def __dir__(self) -> Any: ...
    def __enter__(self) -> Any: ...
    def __eq__(self, other: object) -> bool: ...
    def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> Any: ...
    def __float__(self) -> float: ...
    def __ge__(self, other: object) -> bool: ...
    def __getitem__(self, index: Any) -> Any: ...
    def __gt__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __int__(self) -> int: ...
    def __iter__(self) -> Any: ...
    def __le__(self, other: object) -> bool: ...
    def __len__(self) -> int: ...
    def __lt__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __radd__(self, other: Any) -> Any: ...
    def __rsub__(self, other: Any) -> Any: ...
    def __setattr__(self, name: Any, value: Any) -> Any: ...
    def __setitem__(self, index: Any, object: Any) -> None: ...
    def __sub__(self, other: Any) -> Any: ...

class __CDataFromBuf(_CDataBase): ...

class __CDataGCP(_CDataBase):
    def __del__(self, *args: Any, **kwargs: Any) -> None: ...

class __CDataOwn(_CDataBase):
    def __delitem__(self, other: Any) -> None: ...
    def __getitem__(self, index: Any) -> Any: ...
    def __len__(self) -> int: ...
    def __setitem__(self, index: Any, object: Any) -> None: ...

class __CDataOwnGC(__CDataOwn): ...

class __CData_iterator:
    def __iter__(self) -> Any: ...
    def __next__(self) -> Any: ...

class __FFIGlobSupport: ...

class buffer:
    @classmethod
    def __init__(cls, *args: Any, **kwargs: Any) -> None: ...
    def __delitem__(self, other: Any) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...
    def __getitem__(self, index: Any) -> Any: ...
    def __gt__(self, other: object) -> bool: ...
    def __le__(self, other: object) -> bool: ...
    def __len__(self) -> int: ...
    def __lt__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __setitem__(self, index: Any, object: Any) -> None: ...

def alignof(*args: Any, **kwargs: Any) -> Any: ...
def callback(*args: Any, **kwargs: Any) -> Any: ...
def cast(*args: Any, **kwargs: Any) -> Any: ...
def complete_struct_or_union(*args: Any, **kwargs: Any) -> Any: ...
def from_buffer(*args: Any, **kwargs: Any) -> Any: ...
def from_handle(*args: Any, **kwargs: Any) -> Any: ...
def gcp(*args: Any, **kwargs: Any) -> Any: ...
def get_errno(*args: Any, **kwargs: Any) -> Any: ...
def getcname(*args: Any, **kwargs: Any) -> Any: ...
def load_library(*args: Any, **kwargs: Any) -> Any: ...
def memmove(*args: Any, **kwargs: Any) -> Any: ...
def new_array_type(*args: Any, **kwargs: Any) -> Any: ...
def new_enum_type(*args: Any, **kwargs: Any) -> Any: ...
def new_function_type(*args: Any, **kwargs: Any) -> Any: ...
def new_pointer_type(*args: Any, **kwargs: Any) -> Any: ...
def new_primitive_type(*args: Any, **kwargs: Any) -> Any: ...
def new_struct_type(*args: Any, **kwargs: Any) -> Any: ...
def new_union_type(*args: Any, **kwargs: Any) -> Any: ...
def new_void_type(*args: Any, **kwargs: Any) -> Any: ...
def newp(*args: Any, **kwargs: Any) -> Any: ...
def newp_handle(*args: Any, **kwargs: Any) -> Any: ...
def rawaddressof(*args: Any, **kwargs: Any) -> Any: ...
def release(*args: Any, **kwargs: Any) -> Any: ...
def set_errno(*args: Any, **kwargs: Any) -> Any: ...
def sizeof(*args: Any, **kwargs: Any) -> Any: ...
def string(*args: Any, **kwargs: Any) -> Any: ...
def typeof(*args: Any, **kwargs: Any) -> Any: ...
def typeoffsetof(*args: Any, **kwargs: Any) -> Any: ...
def unpack(*args: Any, **kwargs: Any) -> Any: ...
