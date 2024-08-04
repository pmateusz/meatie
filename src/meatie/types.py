#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Union, runtime_checkable

from typing_extensions import Literal

Method = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]

Duration = float
Time = float

MINUTE = 60
HOUR = 3600
DAY = 86400

INF = float("inf")


@dataclass()  # TODO: change to an ordinary class
class Request:
    method: Method
    path: str
    params: dict[str, Union[str, int]]
    headers: dict[str, Union[str, bytes]]
    data: Optional[Union[str, bytes]] = None
    json: Any = None


@runtime_checkable
class AsyncResponse(Protocol):
    @property
    def status(self) -> int:
        ...

    async def read(self) -> bytes:
        ...

    async def text(self) -> str:
        ...

    async def json(self) -> dict[str, Any]:
        ...


@runtime_checkable
class Response(Protocol):
    @property
    def status(self) -> int:
        ...

    def read(self) -> bytes:
        ...

    def text(self) -> str:
        ...

    def json(self) -> dict[str, Any]:
        ...
