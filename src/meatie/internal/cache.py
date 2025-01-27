#  Copyright 2023 The Meatie Authors. All rights reserved.
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
    def __init__(self, max_size: int = 100) -> None:
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

        self._storage.move_to_end(key)  # Mark as most recently used
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
        to_remove = len(self._storage) - self._max_size
        for _ in range(to_remove):
            # Remove first (oldest) item - OrderedDict maintains insertion order
            self._storage.popitem(last=False)
