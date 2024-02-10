#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from typing import Optional, Union

from meatie import AsyncResponse, Response, Time


class RetryContext:
    __slots__ = ("attempt_number", "started_at", "error", "response")

    def __init__(
        self,
        attempt_number: int,
        started_at: Time,
        error: Optional[BaseException] = None,
        response: Optional[Union[Response, AsyncResponse]] = None,
    ) -> None:
        self.attempt_number = attempt_number
        self.started_at = started_at
        self.error: Optional[BaseException] = error
        self.response: Optional[Union[Response, AsyncResponse]] = response
