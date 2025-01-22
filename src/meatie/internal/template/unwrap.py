from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Unwrappable(Protocol):
    def unwrap(self) -> dict[str, Any]:
        ...
