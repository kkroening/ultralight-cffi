import _cffi_backend

class FFI(_cffi_backend.FFI):
    @staticmethod
    def barf(arg0: int, arg1: int, /) -> str: ...

ffi: FFI

class Lib(_cffi_backend.Lib):
    @staticmethod
    def ulCreateStringUTF8(data: bytes, length: int, /) -> str: ...
