#  Copyright 2025 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional

import httpx
from typing_extensions import Self

from meatie import (
    BaseAsyncClient,
    Cache,
    MeatieError,
    ProxyError,
    RequestError,
    ServerError,
    Timeout,
    TransportError,
)
from meatie.types import Request

from .async_response import AsyncResponse
from .client import build_kwargs


class AsyncClient(BaseAsyncClient):
    """The async client implementation for httpx."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        client_params: Optional[dict[str, Any]] = None,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Any] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__(local_cache, limiter)

        self.client = client
        self.client_params = client_params if client_params else {}
        self.prefix = prefix

    async def send(self, request: Request) -> AsyncResponse:
        kwargs = build_kwargs(request, self.client_params)

        path = request.path
        if self.prefix is not None:
            path = self.prefix + path

        try:
            response = await self.client.request(request.method, path, **kwargs)
        except (httpx.InvalidURL, httpx.UnsupportedProtocol) as exc:
            raise RequestError() from exc
        except httpx.ProxyError as exc:
            raise ProxyError() from exc
        except httpx.TimeoutException as exc:
            raise Timeout() from exc
        except (httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            raise ServerError() from exc
        except (httpx.TooManyRedirects, httpx.ProtocolError) as exc:
            raise TransportError() from exc
        except httpx.HTTPError as exc:
            raise MeatieError() from exc
        return AsyncResponse(response)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.client.aclose()
