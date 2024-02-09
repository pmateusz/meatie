#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import time as sys_time
from dataclasses import dataclass
from typing import Any

from meatie import Duration, Time

__all__ = ["Cache"]


# TODO: implement limit on storage size to avoid memory leaks using OrderedDict
class Cache:
    def __init__(self) -> None:
        self.__storage: dict[str, _Record] = {}

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


@dataclass()
class _Record:
    value: Any
    expires_at: Time
    last_accessed_at: Time
