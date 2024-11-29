class UltralightError(Exception):
    """Base exception type for Ultralight-specific errors that originate from the
    :mod:`ultralight_cffi.glue` layer.

    Note:
        :mod:`ultralight_cffi.glue` may also raise other standard exception types such
        as :class:`ValueError` for general axiomatic violations, whereas
        :class:`UltralightError` is reserved for errors that are more specific to
        Ultralight.

    See also:
        :class:`UltralightJSError` and :class:`UltralightULError`: Error types that
        originate directly from Ultralight itself, such as in the
        :meth:`.._stubs.JSEvaluateScript`, :meth:`..stubs.ulViewEvaluateScript`, etc.
        methods.
    """


__all__ = [
    'UltralightError',
]
