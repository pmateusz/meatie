#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Awaitable, Callable, Optional, Union

from meatie import EndpointDescriptor
from meatie.aio import AsyncEndpointDescriptor
from meatie.internal.types import PT, T

__all__ = ["body"]


class BodyOption:
    __slots__ = ("json", "text")

    def __init__(
        self,
        json: Optional[
            Union[Callable[[Any], dict[str, Any]], Callable[[Any], Awaitable[dict[str, Any]]]]
        ] = None,
        text: Optional[Union[Callable[[Any], str], Callable[[Any], Awaitable[str]]]] = None,
    ) -> None:
        """
        Customize handling of HTTP response body.

        :param json: function to apply on the HTTP response to extract json, otherwise use the default method
         implemented in the client library
        :param text: function to apply on the HTTP response to extract response text, otherwise use the default method
         implemented in the client library
        """

        self.json = json
        self.text = text

    def __call__(
        self, descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
    ) -> None:
        descriptor.get_text = self.text
        descriptor.get_json = self.json


body = BodyOption
