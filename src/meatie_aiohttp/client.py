#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import asyncio
import urllib.parse
from typing import Any, Optional

import aiohttp
from meatie.internal.error import (
    MeatieError,
    ProxyError,
    ServerError,
    Timeout,
    TransportError,
)
from meatie.internal.types import AsyncResponse, Request
from typing_extensions import Self

from . import AiohttpResponse


class AiohttpClient:
    def __init__(
        self, session: aiohttp.ClientSession, session_params: Optional[dict[str, Any]] = None
    ) -> None:
        self.session = session
        self.session_params = session_params if session_params else {}

    async def send(self, request: Request) -> AsyncResponse:
        kwargs: dict[str, Any] = self.session_params.copy()

        if request.data is not None:
            kwargs["data"] = request.data

        if request.json is not None:
            kwargs["json"] = request.json

        if request.headers:
            kwargs["headers"] = request.headers

        if request.query_params:
            kwargs["params"] = urllib.parse.urlencode(request.query_params)

        try:
            response = await self.session.request(request.method, request.path, **kwargs)
        except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError) as exc:
            raise ProxyError(exc) from exc
        except (
            aiohttp.ServerConnectionError,
            aiohttp.ServerDisconnectedError,
            aiohttp.ClientConnectorError,
            aiohttp.ClientConnectionError,
            aiohttp.ClientConnectorSSLError,
            aiohttp.ClientConnectorCertificateError,
        ) as exc:
            raise ServerError(exc) from exc
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError) as exc:
            raise Timeout(exc) from exc
        except (aiohttp.TooManyRedirects, aiohttp.ClientError) as exc:
            raise TransportError(exc) from exc
        except Exception as exc:
            raise MeatieError(exc) from exc
        return AiohttpResponse(response)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        await self.session.close()
