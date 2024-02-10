#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Optional, Union

from meatie import AsyncResponse, Response


class MeatieError(Exception):
    ...


class RetryError(MeatieError):
    ...


class RateLimitExceeded(MeatieError):
    ...


class TransportError(MeatieError):
    ...


class ProxyError(TransportError):
    ...


class ServerError(TransportError):
    ...


class Timeout(ServerError):
    ...


class RequestError(MeatieError):
    ...


class ResponseError(MeatieError):
    def __init__(self, response: Union[Response, AsyncResponse], *args: Any) -> None:
        super().__init__(*args)

        self.response = response


class HttpStatusError(ResponseError):
    ...


class ParseResponseError(ResponseError):
    def __init__(
        self,
        text: str,
        response: Any,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(response, cause)

        self.text = text
