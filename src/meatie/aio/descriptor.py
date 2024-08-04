#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Optional,
    Union,
    overload,
)

from typing_extensions import Self

from meatie import AsyncResponse, Request
from meatie.internal.adapter import TypeAdapter
from meatie.internal.template import RequestTemplate, get_method
from meatie.internal.types import PT, ResponseBodyType

from . import BaseAsyncClient

AsyncOperator = Callable[["AsyncContext[ResponseBodyType]"], Awaitable[ResponseBodyType]]


class AsyncContext(Generic[ResponseBodyType]):
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
        self.response: Optional[AsyncResponse] = None

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


class AsyncEndpointDescriptor(Generic[PT, ResponseBodyType]):
    def __init__(
        self, template: RequestTemplate[Any], response_decoder: TypeAdapter[ResponseBodyType]
    ) -> None:
        self.template = template
        self.response_decoder = response_decoder
        self.get_json: Optional[Callable[[Any], Awaitable[dict[str, Any]]]] = None
        self.get_text: Optional[Callable[[Any], Awaitable[str]]] = None
        self.__operator_by_priority: dict[int, AsyncOperator[ResponseBodyType]] = {}

    def __set_name__(self, owner: type[object], name: str) -> None:
        if self.template.method is not None:
            return

        self.template.method = get_method(name)

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

        return BoundAsyncEndpointDescriptor(  # type: ignore[return-value]
            instance, operators, self.template, self.response_decoder, self.get_json, self.get_text
        )


class BoundAsyncEndpointDescriptor(Generic[PT, ResponseBodyType]):
    def __init__(
        self,
        instance: BaseAsyncClient,
        operators: Iterable[AsyncOperator[ResponseBodyType]],
        template: RequestTemplate[Any],
        response_decoder: TypeAdapter[ResponseBodyType],
        get_json: Optional[Callable[[Any], Awaitable[dict[str, Any]]]],
        get_text: Optional[Callable[[Any], Awaitable[str]]],
    ) -> None:
        self.__instance = instance
        self.__operators = list(operators)
        self.__operators.append(self.__send_request)
        self.__template = template
        self.__response_decoder = response_decoder
        self.__get_json = get_json
        self.__get_text = get_text

    async def __call__(self, *args: PT.args, **kwargs: PT.kwargs) -> ResponseBodyType:
        request = self.__template.build_request(*args, **kwargs)
        context = AsyncContext[ResponseBodyType](self.__instance, self.__operators, request)
        return await context.proceed()

    async def __send_request(self, context: AsyncContext[ResponseBodyType]) -> ResponseBodyType:
        response = await self.__instance.send(context.request)
        if self.__get_json is not None:
            response.get_json = self.__get_json
        if self.__get_text is not None:
            response.get_text = self.__get_text
        context.response = response
        return await self.__response_decoder.from_async_response(response)
