import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class _Record:
    value: Any
    expires_at: float


class Cache:
    def __init__(self, max_size: Optional[int] = None) -> None:
        self._storage: OrderedDict[str, _Record] = OrderedDict()
        self._max_size = max_size
        self._time_provider = time.monotonic

    def load(self, key: str) -> Any:
        """Load a value from the cache."""
        record = self._storage.get(key)
        if record is None:
            return None

        if record.expires_at < self._time_provider():
            del self._storage[key]
            return None

        # Move to end to mark as recently used
        self._storage.move_to_end(key)
        return record.value

    def store(self, key: str, value: Any, ttl: float) -> None:
        """Store a value in the cache."""
        self._storage[key] = _Record(value=value, expires_at=self._time_provider() + ttl)
        # New items are automatically at the end in OrderedDict

        if self._max_size and len(self._storage) > self._max_size:
            self._cleanup()

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        self._storage.pop(key, None)

    def _cleanup(self) -> None:
        """First remove the expired items, then remove the oldest items until max_size is met."""
        # 1. Remove expired items
        now = self._time_provider()
        expired = [key for key, record in self._storage.items() if record.expires_at < now]
        for key in expired:
            del self._storage[key]

        # 2. Remove the oldest items until max_size is met
        while len(self._storage) > self._max_size:
            # Remove first (oldest) item - OrderedDict maintains insertion order
            self._storage.popitem(last=False)
