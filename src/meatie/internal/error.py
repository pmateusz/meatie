#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Optional


class MeatieError(Exception):
    ...


class RateLimitExceeded(MeatieError):
    ...


class ResponseError(MeatieError):
    __slots__ = ("status", "message")

    def __init__(self, status: int, message: Optional[str]) -> None:
        """
        :param status: HTTP status code
        :param message: Message of the response
        """

        self.status = status
        self.message = message


class ParseResponseError(ResponseError):
    ...
