from .. import _bindings
from .. import _ffi
from .. import _stubs
from collections.abc import Generator
from contextlib import contextmanager


def decode(
    jstr: _stubs.JSStringRef,
    strict: bool = True,
) -> str:
    """Decodes an Ultralight JavaScript string (:class:`JSStringRef`) into an ordinary
    Python string.

    This function converts a :class:`JSStringRef` object from Ultralight's
    JavaScriptCore interface into a Python string. It handles the UTF-16 encoding used
    by :class:`JSStringRef` and returns the decoded Unicode string.

    This method is the reverse of :func:`encode`.

    Args:
        jstr: The JavaScript string reference to decode.
        strict: If True, null string pointers raise :class:`ValueError`; otherwise, null
            JS string pointers become an empty Python string.

    Returns:
        The decoded Python Unicode string.

    Raises:
        ValueError: If the :class:`JSStringRef` contains invalid UTF-16 data and
        decoding fails.

    See Also:
        - :func:`encode`: Encodes a Python string into a `JSStringRef`.

    Example:
        >>> with ultra.js_str.scoped('Hello!') as jstr:
        ...     print(ultra.js_str.decode(jstr))
        Hello!
    """
    if strict and jstr == _ffi.NULL:
        raise ValueError('Encountered null pointer while expecting a JavaScript string')

    str_ptr = _stubs.JSStringGetCharactersPtr(jstr)
    str_len = _stubs.JSStringGetLength(jstr)
    buffer = _bindings.ffi.buffer(str_ptr, str_len * 2)  # each UTF-16 char is 2 bytes
    buffer_view = buffer[:]
    result: str = buffer_view.decode('utf-16')
    return result


def encode(
    text: str,
) -> _stubs.JSStringRef:
    """Encodes an ordinary Python string into an Ultralight JavaScript string
    (:class:`JSStringRef`).

    This method is the reverse of :func:`decode`.

    Warning:
        Care must be taken to avoid memory leaks. Prefer using :func:`scoped` to
        automatically manage the lifecycle of the :class:`JSStringRef` object. If you
        use :func:`encode`, it is your responsibility to call
        `ultralight_cffi.JSStringRelease` on the returned object when it's no longer
        needed.

    Args:
        text: The Python string to encode.

    Returns:
        A :class:`JSStringRef` representing the encoded string.

    See Also:
        - :func:`decode`: Decodes a :class:`JSStringRef` back into a Python string.
        - :func:`scoped`: Safely manages the lifecycle of a :class:`JSStringRef`.

    Example:
        >>> jstr = encode('Hello!')
        ... print(decode(jstr))
        Hello!
        >>> ultra.JSStringRelease(jstr)  # Prevent memory leaks
    """
    return _stubs.JSStringCreateWithUTF8CString(text.encode())


@contextmanager
def scoped(
    text: _stubs.JSStringRef | str,
) -> Generator[_stubs.JSStringRef, None, None]:
    """Context manager that creates/retains a JS string reference and releases it when
    the context exits.

    If the text is an ordinary Python string, it's converted to a JS string via
    :func:`encode`.  Otherwise is the text is already a JS string, its reference count
    is increased by calling :func:`JSStringRetain`.  Regardless, a reference is retained
    in either case for the life of the context, and automatically released when the
    context exits.

    Warning:
        While inside the context, the :class:`JSStringRef` can be safely used. However,
        attempting to access the :class:`JSStringRef` after the context has exited will
        result in undefined (i.e. likely catastrophic) behavior, as the object will have
        been released.

    Args:
        text: The JS string to retain, or a Python string to encode into a JS string.

    Yields:
        The encoded JavaScript string reference.

    Example::

        >>> with scoped('Hello!') as jstr:
        ...     print(decode(jstr))
        Hello!
    """
    jstr = encode(text) if isinstance(text, str) else _stubs.JSStringRetain(text)
    try:
        yield jstr
    finally:
        _stubs.JSStringRelease(jstr)


__all__ = [
    'decode',
    'encode',
    'scoped',
]
