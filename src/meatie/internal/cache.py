#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import time as sys_time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional

from meatie import Duration, Time

__all__ = ["Cache"]


class Cache:
    def __init__(self, max_size: Optional[int] = None) -> None:
        self.__storage: OrderedDict[str, _Record] = OrderedDict()
        self.max_size = max_size

    def load(self, key: str) -> Any:
        current_time = sys_time.monotonic()
        return self.load_at(current_time, key)

    def load_at(self, time: Time, key: str) -> Any:
        record_opt = self.__storage.get(key)
        if record_opt is None:
            return None

        if record_opt.expires_at < time:
            del self.__storage[key]
            return None

        record_opt.last_accessed_at = time
        return record_opt.value

    def store(self, key: str, value: Any, ttl: Duration) -> None:
        current_time = sys_time.monotonic()
        self.store_at(current_time, key, value, ttl)

    def store_at(self, time: Time, key: str, value: Any, ttl: Duration) -> Any:
        self.__storage[key] = _Record(value=value, expires_at=time + ttl, last_accessed_at=time)

        # Reduce the cache size by 20% if the max size is reached, the use of "while" is intentional
        if self.max_size is not None and len(self.__storage) > self.max_size:
            self.__reduce_size()

    def __reduce_size(self) -> None:
        """Remove expired records from the cache. If this is not enough to reach 20% free space, remove the oldest records in the cache."""
        target_size = int(self.max_size * 0.8)

        current_time = sys_time.monotonic()
        expired_keys = [
            key for key, record in self.__storage.items() if record.expires_at < current_time
        ]

        for key in expired_keys:
            del self.__storage[key]

        while len(self.__storage) > target_size:
            self.__storage.popitem(last=False)


@dataclass()
class _Record:
    value: Any
    expires_at: Time
    last_accessed_at: Time
