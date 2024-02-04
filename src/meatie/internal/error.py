#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Optional, Union

from meatie.internal.types import AsyncResponse, Response


class MeatieError(Exception):
    def __init__(self, cause: Optional[BaseException] = None) -> None:
        self.cause = cause


class RateLimitExceeded(MeatieError):
    ...


class ResponseError(MeatieError):
    def __init__(
        self, response: Union[Response, AsyncResponse], cause: Optional[BaseException] = None
    ) -> None:
        super().__init__(cause)

        self.response = response


class TransportError(MeatieError):
    ...


class ParseResponseError(ResponseError):
    ...
