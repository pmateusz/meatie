#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Optional,
    Protocol,
    Union,
    get_args,
    overload,
    runtime_checkable,
)

from aiohttp import ClientResponse
from typing_extensions import Self

from meatie.aio import (
    Client,
    Method,
    Operator,
    Request,
)
from meatie.internal.types import PT

from .request_template import RequestTemplate, ResponseBodyT


class EndpointDescriptor(Generic[PT, ResponseBodyT]):
    __slots__ = (
        "template",
        "__content_decoder",
        "__operator_by_priority",
    )

    def __init__(self, template: RequestTemplate[Any, ResponseBodyT]) -> None:
        self.template = template
        self.__operator_by_priority: dict[int, Operator[Client, ResponseBodyT]] = {}

    def __set_name__(self, owner: type[object], name: str) -> None:
        if self.template.method is not None:
            return

        method_opt = _get_method_opt(name)
        if method_opt is None:
            # Python interactions with class descriptors doesn't allow to return an error message to the user,
            # we assume the GET method
            method_opt = "GET"

        self.template.method = method_opt

    def register_operator(self, priority: int, operator: Operator[Client, ResponseBodyT]) -> None:
        self.__operator_by_priority[priority] = operator

    @overload
    def __get__(self, instance: None, owner: None) -> Self:
        ...

    @overload
    def __get__(
        self, instance: Client, owner: type[object]
    ) -> Callable[PT, Awaitable[ResponseBodyT]]:
        ...

    def __get__(
        self, instance: Optional[Client], owner: Optional[type[object]] = None
    ) -> Union[Self, Callable[PT, Awaitable[ResponseBodyT]]]:
        if instance is None or owner is None:
            return self

        priority_operator_pair = list(self.__operator_by_priority.items())
        priority_operator_pair.sort()
        operators = [operator for _, operator in priority_operator_pair]

        return _BoundEndpointDescriptor(  # type: ignore[return-value]
            instance, operators, self.template
        )


_method_pattern_pairs = [
    (method, re.compile("^" + method, re.IGNORECASE)) for method in get_args(Method)
]


def _get_method_opt(name: str) -> Optional[Method]:
    for method, pattern in _method_pattern_pairs:
        if re.match(pattern, name):
            return method
    return None


@runtime_checkable
class EndpointOption(Protocol):
    def __call__(self, endpoint: EndpointDescriptor[PT, ResponseBodyT]) -> None:
        ...


class _Context(Generic[ResponseBodyT]):
    def __init__(
        self, client: Client, operators: list[Operator[Client, ResponseBodyT]], request: Request
    ) -> None:
        self.client = client
        self.__operators = operators
        self.__next_step = 0

        self.request = request
        self.response: Optional[ClientResponse] = None

    async def proceed(self) -> ResponseBodyT:
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


class _BoundEndpointDescriptor(Generic[PT, ResponseBodyT]):
    def __init__(
        self,
        instance: Client,
        operators: Iterable[Operator[Client, ResponseBodyT]],
        template: RequestTemplate[Any, ResponseBodyT],
    ) -> None:
        self.__instance = instance
        self.__operators = list(operators)
        self.__operators.append(self.__make_request)  # type: ignore[arg-type]
        self.__template = template

    async def __call__(self, *args: PT.args, **kwargs: PT.kwargs) -> ResponseBodyT:
        request = self.__template.build_request(*args, **kwargs)
        context = _Context[ResponseBodyT](self.__instance, self.__operators, request)
        return await context.proceed()

    async def __make_request(self, context: _Context[ResponseBodyT]) -> ResponseBodyT:
        response = await self.__instance.make_request(context.request)
        context.response = response
        return await self.__template.response_decoder.from_response(response)
