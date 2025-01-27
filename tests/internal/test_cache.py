#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from meatie.internal.cache import Cache
from typing_extensions import override


class TimedCache(Cache):
    def __init__(self, max_size: int) -> None:
        super().__init__(max_size)
        self.current_time = 0.0

    @override
    def _now(self) -> float:
        return self.current_time


def test_store_and_load() -> None:
    # GIVEN a cache with no stored items
    cache = TimedCache(max_size=1)

    # WHEN a value is stored with the key "key1"
    cache.store("key1", "value1", ttl=10)

    # THEN the value for key "key1" should be retrievable
    assert cache.load("key1") == "value1"


def test_load_nonexistent() -> None:
    # GIVEN a cache with no stored items
    cache = TimedCache(max_size=1)

    # WHEN-THEN the result should be None
    assert cache.load("nonexistent") is None


def test_expiration() -> None:
    # GIVEN a cache where the current time is 100
    cache = TimedCache(max_size=1)

    # WHEN a value with ttl of 10 seconds is stored
    cache.store("key1", "value1", ttl=10)
    # THEN the value for key "key1" should be retrievable
    assert cache.load("key1") == "value1"

    # Advance time past expiration
    cache.current_time = 100
    # WHEN trying to load the expired key "key1"
    # THEN it should return None as it has expired
    assert cache.load("key1") is None


def test_max_size() -> None:
    # GIVEN a cache with max size of 2
    cache = TimedCache(max_size=2)

    # WHEN 3 items are stored in the cache
    cache.store("key1", "value1", ttl=10)
    cache.store("key2", "value2", ttl=10)
    cache.store("key3", "value3", ttl=10)

    # THEN only the 2 most recent items should remain
    assert cache.load("key1") is None
    assert cache.load("key2") == "value2"
    assert cache.load("key3") == "value3"


def test_delete() -> None:
    # GIVEN a cache with one stored item
    cache = TimedCache(max_size=2)
    cache.store("key1", "value1", ttl=10)

    # WHEN the key "key1" is deleted
    cache.delete("key1")

    # THEN the value for "key1" should no longer be retrievable
    assert cache.load("key1") is None


def test_cleanup_expired_before_old() -> None:
    # GIVEN a cache with a max size of 3 and current time as 100
    cache = TimedCache(max_size=3)
    cache.current_time = 100.0

    # WHEN a mix of expired and valid items are stored
    cache.store("expired", "value1", ttl=5)  # Expires at 105
    cache.store("valid1", "value2", ttl=20)  # Expires at 120
    cache.store("valid2", "value3", ttl=20)  # Expires at 120

    # Advance time so first item expires
    cache.current_time = 110

    # WHEN another item is added to the cache
    cache.store("valid3", "value4", ttl=20)

    # THEN expired items should be cleaned up first, and valid items should remain
    assert cache.load("expired") is None
    assert cache.load("valid1") == "value2"
    assert cache.load("valid2") == "value3"
    assert cache.load("valid3") == "value4"
