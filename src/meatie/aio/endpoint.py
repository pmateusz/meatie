#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from collections.abc import Callable
from typing import (
    Any,
    Awaitable,
    Optional,
)

from meatie import Method
from meatie.aio import EndpointDescriptor, PathTemplate, RequestTemplate
from meatie.internal import PT, T


def endpoint(
    path: str,
    *args: Any,
    method: Optional[Method] = None,
) -> Callable[[Callable[PT, Awaitable[T]]], Callable[PT, Awaitable[T]]]:
    def class_descriptor(
        func: Callable[PT, Awaitable[T]],
    ) -> Callable[PT, Awaitable[T]]:
        path_template = PathTemplate.from_string(path)
        request_template: RequestTemplate[Any, T] = RequestTemplate.from_callable(
            func, path_template, method
        )
        descriptor = EndpointDescriptor[PT, T](request_template)

        for option in args:
            option(descriptor)

        return descriptor  # type: ignore[return-value]

    return class_descriptor
