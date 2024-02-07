#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Optional,
    Union,
    get_args,
    overload,
)

from aiohttp import ClientResponse
from typing_extensions import Self

from meatie import Method, Request, RequestTemplate
from meatie.aio import (
    AsyncOperator,
    BaseAsyncClient,
)
from meatie.aio.adapter import AsyncTypeAdapter
from meatie.internal.types import PT, ResponseBodyType


class EndpointDescriptor(Generic[PT, ResponseBodyType]):

    def __init__(self, template: RequestTemplate[Any], response_decoder: AsyncTypeAdapter[ResponseBodyType]) -> None:
        self.template = template
        self.response_decoder = response_decoder
        self.__operator_by_priority: dict[int, AsyncOperator[ResponseBodyType]] = {}

    def __set_name__(self, owner: type[object], name: str) -> None:
        if self.template.method is not None:
            return

        method_opt = _get_method_opt(name)
        if method_opt is None:
            # Python interactions with class descriptors doesn't allow to return an error message to the user,
            # we assume the GET method
            method_opt = "GET"

        self.template.method = method_opt

    def register_operator(self, priority: int, operator: AsyncOperator[ResponseBodyType]) -> None:
        self.__operator_by_priority[priority] = operator

    @overload
    def __get__(self, instance: None, owner: None) -> Self:
        ...

    @overload
    def __get__(
        self, instance: BaseAsyncClient, owner: type[object]
    ) -> Callable[PT, Awaitable[ResponseBodyType]]:
        ...

    def __get__(
        self, instance: Optional[BaseAsyncClient], owner: Optional[type[object]] = None
    ) -> Union[Self, Callable[PT, Awaitable[ResponseBodyType]]]:
        if instance is None or owner is None:
            return self

        priority_operator_pair = list(self.__operator_by_priority.items())
        priority_operator_pair.sort()
        operators = [operator for _, operator in priority_operator_pair]

        return BoundEndpointDescriptor(  # type: ignore[return-value]
            instance, operators, self.template, self.response_decoder
        )


_method_pattern_pairs = [
    (method, re.compile("^" + method, re.IGNORECASE)) for method in get_args(Method)
]


def _get_method_opt(name: str) -> Optional[Method]:
    for method, pattern in _method_pattern_pairs:
        if re.match(pattern, name):
            return method
    return None


class AsyncContextImpl(Generic[ResponseBodyType]):
    def __init__(
        self,
        client: BaseAsyncClient,
        operators: list[AsyncOperator[ResponseBodyType]],
        request: Request,
    ) -> None:
        self.client = client
        self.__operators = operators
        self.__next_step = 0

        self.request = request
        self.response: Optional[ClientResponse] = None

    async def proceed(self) -> ResponseBodyType:
        if self.__next_step >= len(self.__operators):
            raise RuntimeError("No more step to process request")

        current_step = self.__next_step
        self.__next_step += 1
        current_operator = self.__operators[current_step]
        try:
            result = await current_operator(self)
            return result
        finally:
            self.__next_step = current_step


class BoundEndpointDescriptor(Generic[PT, ResponseBodyType]):
    def __init__(
        self,
        instance: BaseAsyncClient,
        operators: Iterable[AsyncOperator[ResponseBodyType]],
        template: RequestTemplate[Any],
        response_decoder: AsyncTypeAdapter[ResponseBodyType],
    ) -> None:
        self.__instance = instance
        self.__operators = list(operators)
        self.__operators.append(self.__make_request)  # type: ignore[arg-type]
        self.__template = template
        self.__response_decoder = response_decoder

    async def __call__(self, *args: PT.args, **kwargs: PT.kwargs) -> ResponseBodyType:
        request = self.__template.build_request(*args, **kwargs)
        context = AsyncContextImpl[ResponseBodyType](self.__instance, self.__operators, request)
        return await context.proceed()

    async def __make_request(self, context: AsyncContextImpl[ResponseBodyType]) -> ResponseBodyType:
        response = await self.__instance.send(context.request)
        context.response = response
        return await self.__response_decoder.from_response(response)
