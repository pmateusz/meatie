#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from abc import abstractmethod
from typing import Any, Optional, TypeVar

from typing_extensions import Self

from meatie.internal.cache import Cache
from meatie.internal.limit import Limiter, Rate
from meatie.types import INF, Request


class BaseClient:
    """Base class for the integration with HTTP client libraries."""

    SHARED_CACHE_MAX_SIZE: int = 1000
    shared_cache: Cache

    def __init__(
        self,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Limiter] = None,
    ):
        """Creates a BaseClient.

        Args:
            local_cache: Cache implementation for storing the HTTP responses.
            limiter: Rate limiter used for throttling the rate of sending the HTTP requests.
        """
        self.local_cache = local_cache if local_cache is not None else Cache()
        self.limiter = limiter if limiter is not None else Limiter(Rate.max, INF)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls.shared_cache = Cache(max_size=cls.SHARED_CACHE_MAX_SIZE)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        return None

    def authenticate(self, request: Request) -> None:
        """Method called by the Meatie before sending an HTTP request for an endpoint marked as private.

        The method could be used to set the Authorization header or sign the HTTP request and using API keys.

        Args:
            request: HTTP request object.
        """
        pass

    @abstractmethod
    def send(self, request: Request) -> Any:
        """Sends an HTTP request using the underlying HTTP client library.

        Returns:
            HTTP response object from the underlying HTTP client library.
        """
        ...


ClientType = TypeVar("ClientType", bound=BaseClient)
