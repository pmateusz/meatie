from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Unwrappable(Protocol):
    """Marker interface for query parameters that require custom serialization logic."""

    def unwrap(self) -> dict[str, Any]:
        """Meatie will call this method on an object passed as a query parameter.

        Returns:
            A dictionary of query parameters. Value types should be supported by the underlying HTTP client library.
        """
        ...
