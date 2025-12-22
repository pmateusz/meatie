#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from collections.abc import Callable
from typing import (
    Any,
    Optional,
    Union,
    cast,
    get_type_hints,
)

from meatie.aio import AsyncEndpointDescriptor
from meatie.descriptor import EndpointDescriptor
from meatie.internal.adapter import TypeAdapter, get_adapter
from meatie.internal.template import PathTemplate, RequestTemplate
from meatie.internal.types import PT, T
from meatie.types import Method


def endpoint(
    path: str,
    *args: Any,
    method: Optional[Method] = None,
) -> Callable[[Callable[PT, T]], Callable[PT, T]]:
    """Class descriptor for decorating methods that represent API endpoints.

    Inspects the method signature to create an endpoint descriptor that can be used to make HTTP requests.

    Parameters:
        path: URL path template. It should start with `/`. Path parameters should be surrounded by parentheses.
        args: options to customize the endpoint behaviour, such as caching, rate limiting, retries, and authentication.
        method: HTTP method for making the request. Inferred from the method name by default.

    Returns:
        A decorator that preserves the callable signature of the decorated method.
        For async methods, returns a callable with Awaitable return type.
        For sync methods, returns a callable with direct return type.

    Examples:
        ```python
        from typing import Annotated

        from aiohttp import ClientSession
        from meatie import api_ref, endpoint
        from meatie_aiohttp import Client

        class JsonPlaceholderClient(Client):
            def __init__(self) -> None:
                super().__init__(ClientSession(base_url="https://jsonplaceholder.typicode.com"))

            @endpoint("/todos")
            async def get_todos(self, user_id: Annotated[int, api_ref("userId")] = None) -> list[dict]: ...

            @endpoint("/users/{user_id}/todos")
            async def get_todos_by_user(self, user_id: int) -> list[dict]: ...
        ```
    """

    def class_descriptor(func: Callable[PT, T]) -> Callable[PT, T]:
        path_template = PathTemplate.from_string(path)

        signature = inspect.signature(func)
        type_hints = get_type_hints(func, include_extras=True)
        request_template: RequestTemplate[Any] = RequestTemplate.from_signature(
            signature, type_hints, path_template, method
        )

        return_type = type_hints["return"]
        response_decoder: TypeAdapter[T] = get_adapter(return_type)

        is_coroutine = inspect.iscoroutinefunction(func)
        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
        if is_coroutine:
            descriptor = AsyncEndpointDescriptor[PT, T](request_template, response_decoder)
        else:
            descriptor = EndpointDescriptor[PT, T](request_template, response_decoder)

        for option in args:
            option(descriptor)

        # Cast the descriptor to the expected callable type.
        # The descriptor protocol ensures this works at runtime: when accessed on an instance,
        # the descriptor's __get__ method returns a bound callable with the correct signature.
        return cast(Callable[PT, T], descriptor)

    return class_descriptor
