from __future__ import annotations

import dataclasses
from .. import _ffi
from .. import _stubs
from . import js_str
from dataclasses import dataclass
from types import TracebackType
from typing import Self


@dataclass(frozen=True)
class JSContext:
    ref: _stubs.JSContextRef


@dataclass(frozen=True)
class JSGlobalContext(JSContext):
    ref: _stubs.JSGlobalContextRef

    _newly_created: bool = dataclasses.field(compare=False, default=False)
    """Internally tracks whether this context object refers to a newly created context,
    in order to decide whether to perform ``JSGlobalContextRetain`` in
    :meth:`__enter__`.
    """

    def get_name(self) -> str:
        """Gets the name of a global JavaScript context."""
        name_jstr = _stubs.JSGlobalContextCopyName(self.ref)
        try:
            name_pystr = js_str.decode(name_jstr)
        finally:
            _stubs.JSStringRelease(name_jstr)
        return name_pystr

    def set_name(
        self,
        name: str,
    ) -> None:
        """Sets the name of a global JavaScript context."""
        with js_str.scoped(name) as name_jstr:
            _stubs.JSGlobalContextSetName(self.ref, name_jstr)

    def get_memory_usage_statistics(self) -> _js_obj.JSObject:
        stats_obj_ref = _stubs.JSGetMemoryUsageStatistics(self.ref)
        return _js_obj.JSObject(stats_obj_ref, self)

    def get_protected_object_count(self) -> int:
        """Convenience method for getting the number of protected objects, according to
        the memory usage stats.
        """
        return (
            self.get_memory_usage_statistics()
            .get_property('protectedObjectCount')
            .to_int()
        )

    @classmethod
    def new(cls) -> Self:
        ref = _stubs.JSGlobalContextCreate(_ffi.NULL)
        return cls(ref, _newly_created=True)

    def __enter__(self) -> Self:
        if self._newly_created:
            # If the context was freshly created with `JSGlobalContext.new()`, avoid re-
            # retaining it since this context object already owns the pointer.
            #
            # Note: This dataclass is semantically immutable with `frozen=True`, but we
            # violate that assumption here due to a practical tradeoff.  The pure
            # approach would be to return a modified object with
            # `dataclasses.replace(self, _newly_created=True)` and everything should
            # work just fine as long as the caller plays by the rules by holding the
            # new dataclass reference, but just in case they don't, setting the value
            # here makes double-free situations less likely with misbehaved callers.
            # `_newly_created` is not part of the comparison/hash consideration and is
            # only used between calling `new()` and `__enter__()` so it's a negligible
            # purity cost for greater safety.
            object.__setattr__(self, '_newly_created', False)
        else:
            # If the context is re-entered or constructed from an existing reference,
            # then the retain/release calls stack.
            _stubs.JSGlobalContextRetain(self.ref)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        _stubs.JSGlobalContextRelease(self.ref)


from . import _js_obj  # pylint: disable=cyclic-import,wrong-import-position

__all__ = [
    'JSContext',
    'JSGlobalContext',
]
