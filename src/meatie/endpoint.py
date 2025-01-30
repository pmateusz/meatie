#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from collections.abc import Callable
from typing import (
    Any,
    Optional,
    Union,
    get_type_hints,
)

from meatie import AsyncEndpointDescriptor, EndpointDescriptor, Method
from meatie.internal.adapter import TypeAdapter, get_adapter
from meatie.internal.template import PathTemplate, RequestTemplate
from meatie.internal.types import PT, T


def endpoint(
    path: str,
    *args: Any,
    method: Optional[Method] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Class descriptor for decorating methods whose signature represents an API endpoint.

    Inspects the method signature to create an endpoint descriptor that can be used to make HTTP requests.

    Args:
        path: URL path template, it should start with `/` and path parameters should be surrounded by parentheses.
        args: optional parameters to customize the behavior of the endpoint, such as caching, rate limiting, retries, and authentication.
        method: HTTP method to use when making the request, if not set the method is inferred from the method name.

    Returns:
        Endpoint class descriptor.
    """

    def class_descriptor(func: Callable[PT, T]) -> Callable[PT, T]:
        path_template = PathTemplate.from_string(path)

        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        request_template: RequestTemplate[T] = RequestTemplate.from_signature(
            signature, type_hints, path_template, method
        )

        return_type = type_hints["return"]
        response_decoder: TypeAdapter[T] = get_adapter(return_type)

        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
        is_coroutine = inspect.iscoroutinefunction(func)
        if is_coroutine:
            descriptor = AsyncEndpointDescriptor[PT, T](request_template, response_decoder)
        else:
            descriptor = EndpointDescriptor[PT, T](request_template, response_decoder)

        for option in args:
            option(descriptor)

        return descriptor  # type: ignore[return-value]

    return class_descriptor
