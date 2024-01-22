#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.


from typing import Any, Awaitable, Callable, Optional, Protocol, TypeVar

from typing_extensions import Self

from meatie.internal.types import T_Out

from . import Request, Response


class Client(Protocol):
    async def make_request(self, request: Request) -> Response:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        ...


ClientType = TypeVar("ClientType", bound=Client, covariant=True)


class Context(Protocol[ClientType, T_Out]):
    @property
    def client(self) -> ClientType:
        ...

    @property
    def request(self) -> Request:
        ...

    @property
    def response(self) -> Optional[Response]:
        ...

    async def proceed(self) -> T_Out:
        ...


Operator = Callable[[Context[ClientType, T_Out]], Awaitable[T_Out]]
