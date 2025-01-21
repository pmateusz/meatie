import pytest
from meatie.internal.cache import Cache


class TestCache:
    @pytest.fixture
    def cache(self) -> Cache:
        return Cache(max_size=3)

    def test_store_and_load(self, cache):
        cache.store("key1", "value1", ttl=10)
        assert cache.load("key1") == "value1"

    def test_load_nonexistent(self, cache):
        assert cache.load("nonexistent") is None

    def test_expiration(self, cache):
        # Mock time
        current_time = 100
        cache._time_provider = lambda: current_time

        cache.store("key1", "value1", ttl=10)
        assert cache.load("key1") == "value1"

        # Advance time past expiration
        current_time = 111
        assert cache.load("key1") is None

    def test_max_size(self):
        cache = Cache(max_size=2)

        # Store 3 items
        cache.store("key1", "value1", ttl=10)
        cache.store("key2", "value2", ttl=10)
        cache.store("key3", "value3", ttl=10)

        # Should only have 2 newest items
        assert cache.load("key1") is None
        assert cache.load("key2") == "value2"
        assert cache.load("key3") == "value3"

    def test_delete(self, cache):
        cache.store("key1", "value1", ttl=10)
        cache.delete("key1")
        assert cache.load("key1") is None

    def test_cleanup_expired_before_old(self):
        current_time = 100
        cache = Cache(max_size=3)
        cache._time_provider = lambda: current_time

        # Add mix of expired and valid items
        cache.store("expired", "value1", ttl=5)  # Expires at 105
        cache.store("valid1", "value2", ttl=20)  # Expires at 120
        cache.store("valid2", "value3", ttl=20)  # Expires at 120

        # Advance time so first item expires
        current_time = 110

        # Add one more to trigger cleanup
        cache.store("valid3", "value4", ttl=20)

        # Should remove expired item first
        assert cache.load("expired") is None
        assert cache.load("valid1") == "value2"
        assert cache.load("valid2") == "value3"
        assert cache.load("valid3") == "value4"
