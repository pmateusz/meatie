#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from collections.abc import Callable
from inspect import isawaitable
from typing import (
    Any,
    Optional,
    Union,
    get_type_hints,
)

from meatie import Method, PathTemplate, RequestTemplate
from meatie.adapter import TypeAdapter, get_adapter
from meatie.aio import AsyncEndpointDescriptor
from meatie.aio.adapter import AsyncTypeAdapter, get_async_adapter
from meatie.descriptor import EndpointDescriptor
from meatie.internal.types import T


def endpoint(
    path: str,
    *args: Any,
    method: Optional[Method] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def class_descriptor(func: Callable[..., T]) -> Callable[..., T]:
        path_template = PathTemplate.from_string(path)

        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        request_template: RequestTemplate[T] = RequestTemplate.from_signature(
            signature, type_hints, path_template, method
        )

        return_type = type_hints["return"]
        descriptor: Union[EndpointDescriptor[..., T], AsyncEndpointDescriptor[..., T]]
        if isawaitable(func):
            async_response_decoder: AsyncTypeAdapter[T] = get_async_adapter(return_type)
            descriptor = AsyncEndpointDescriptor[..., T](request_template, async_response_decoder)
        else:
            response_decoder: TypeAdapter[T] = get_adapter(return_type)
            descriptor = EndpointDescriptor[..., T](request_template, response_decoder)

        for option in args:
            option(descriptor)

        return descriptor  # type: ignore[return-value]

    return class_descriptor
