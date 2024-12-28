#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import Any, Awaitable, Callable, Optional, Union

from meatie import AsyncResponse, EndpointDescriptor, Response
from meatie.aio import AsyncEndpointDescriptor
from meatie.internal.types import PT, T

__all__ = ["body"]


class BodyOption:
    __slots__ = ("json", "text", "error")

    def __init__(
        self,
        json: Optional[Union[Callable[[Any], Any], Callable[[Any], Awaitable[Any]]]] = None,
        text: Optional[Union[Callable[[Any], str], Callable[[Any], Awaitable[str]]]] = None,
        error: Optional[
            Union[
                Callable[[Response], Optional[Exception]],
                Callable[[AsyncResponse], Awaitable[Optional[Exception]]],
            ]
        ] = None,
    ) -> None:
        """
        Customize handling of HTTP response body.

        :param json: function to apply on the HTTP response to extract json. The default is to rely on the behaviour of the HTTP client library.
        :param text: function to apply on the HTTP response to extract text. The default is to rely on the behaviour of the HTTP client library.
        :param error: function to apply on the HTTP response to extract an error. The default behaviour is to rely on the behaviour of the HTTP client library.
        """

        self.json = json
        self.text = text
        self.error = error

    def __call__(
        self, descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]]
    ) -> None:
        descriptor.get_text = self.text
        descriptor.get_json = self.json
        descriptor.get_error = self.error


body = BodyOption
