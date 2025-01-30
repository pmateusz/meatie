#  Copyright 2025 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class _Record:
    value: Any
    expires_at: float


class Cache:
    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._storage: OrderedDict[str, _Record] = OrderedDict()

    def load(self, key: str) -> Any:
        """Load a value from the cache."""
        record = self._storage.get(key)
        if record is None:
            return None

        if record.expires_at < self._now():
            del self._storage[key]
            return None

        self._storage.move_to_end(key)  # Mark as most recently used
        return record.value

    def store(self, key: str, value: Any, ttl: float) -> None:
        """Store a value in the cache."""
        self._storage[key] = _Record(value=value, expires_at=self._now() + ttl)

        if len(self._storage) > self.max_size:
            self._cleanup()

    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        self._storage.pop(key, None)

    def _now(self) -> float:
        return time.monotonic()

    def _cleanup(self) -> None:
        """First remove the expired items, then remove the oldest items until max_size is met."""
        # remove expired items
        now = self._now()
        expired = [key for key, record in self._storage.items() if record.expires_at < now]
        for key in expired:
            del self._storage[key]

        # remove the oldest items until max_size is met
        to_remove = len(self._storage) - self.max_size
        for _ in range(to_remove):
            self._storage.popitem(last=False)
