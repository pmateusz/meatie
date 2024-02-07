#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from collections.abc import Callable
from typing import (
    Any,
    Awaitable,
    Optional, get_type_hints,
)

from meatie import Method, PathTemplate, RequestTemplate
from meatie.aio import EndpointDescriptor
from meatie.adapter.aio import get_async_adapter
from meatie.internal.types import PT, T


def endpoint(
    path: str,
    *args: Any,
    method: Optional[Method] = None,
) -> Callable[[Callable[PT, Awaitable[T]]], Callable[PT, Awaitable[T]]]:
    def class_descriptor(
        func: Callable[PT, Awaitable[T]],
    ) -> Callable[PT, Awaitable[T]]:
        path_template = PathTemplate.from_string(path)

        # TODO: decide if method should be async or not
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        request_template: RequestTemplate[Any, T] = RequestTemplate.from_signature(
            signature, type_hints, path_template, method
        )

        return_type = type_hints["return"]
        response_decoder = get_async_adapter(return_type)
        descriptor = EndpointDescriptor[PT, T](request_template, response_decoder)

        for option in args:
            option(descriptor)

        return descriptor  # type: ignore[return-value]

    return class_descriptor
