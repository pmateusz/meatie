#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
from typing import Any, Optional

import aiohttp

from meatie import (
    AsyncResponse,
    BaseAsyncClient,
    Cache,
    MeatieError,
    ProxyError,
    Request,
    RequestError,
    ServerError,
    Timeout,
    TransportError,
)

from . import Response


class Client(BaseAsyncClient):
    """The async client implementation for aiohttp."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        session_params: Optional[dict[str, Any]] = None,
        local_cache: Optional[Cache] = None,
        limiter: Optional[Any] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__(local_cache, limiter)

        self.session = session
        self.session_params = session_params if session_params else {}
        self.prefix = prefix

    async def send(self, request: Request) -> AsyncResponse:
        kwargs: dict[str, Any] = self.session_params.copy()

        path = request.path
        if self.prefix is not None:
            path = self.prefix + path

        if request.data is not None:
            kwargs["data"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.params:
            kwargs["params"] = request.params

        try:
            response = await self.session.request(request.method, path, **kwargs)
        except (
            aiohttp.ClientProxyConnectionError,
            aiohttp.ClientHttpProxyError,
        ) as exc:
            raise ProxyError(exc) from exc
        except (
            aiohttp.ServerConnectionError,
            aiohttp.ServerDisconnectedError,
            aiohttp.ClientConnectorError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorSSLError,
            aiohttp.ClientConnectorCertificateError,
        ) as exc:
            raise ServerError() from exc
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as exc:
            raise Timeout() from exc
        except (aiohttp.InvalidURL, aiohttp.NonHttpUrlClientError) as exc:
            raise RequestError() from exc
        except (aiohttp.TooManyRedirects, aiohttp.ClientError) as exc:
            raise TransportError() from exc
        except Exception as exc:
            raise MeatieError() from exc
        return Response(response)

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.close()
