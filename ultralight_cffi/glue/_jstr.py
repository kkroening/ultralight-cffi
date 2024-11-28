from .. import _bindings
from .. import _stubs
from collections.abc import Generator
from contextlib import contextmanager


def jstr_decode(
    jstr: _stubs.JSStringRef,
) -> str:
    str_ptr = _stubs.JSStringGetCharactersPtr(jstr)
    str_len = _stubs.JSStringGetLength(jstr)
    try:
        # Each UTF-16 character is 2 bytes
        buffer = _bindings.ffi.buffer(str_ptr, str_len * 2)
        buffer_view = buffer[:]
        assert isinstance(buffer_view, memoryview)  # FIXME/TBD
        result: str = buffer_view.decode('utf-16')  # type: ignore[attr-defined]
    except UnicodeDecodeError as error:
        raise ValueError(f'Failed to decode UTF-16 string: {error}') from error
    return result


@contextmanager
def jstr_scope(text: str) -> Generator[_stubs.JSStringRef, None, None]:
    jstr = _stubs.JSStringCreateWithUTF8CString(text.encode())
    try:
        yield jstr
    finally:
        _stubs.JSStringRelease(jstr)
