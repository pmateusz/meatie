#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from typing import Any, Awaitable, Callable, Optional, Union

from meatie.aio import AsyncEndpointDescriptor
from meatie.descriptor import EndpointDescriptor
from meatie.internal.types import PT, T
from meatie.types import AsyncResponse, Response

__all__ = ["body"]


class BodyOption:
    """Customize handling of HTTP response body, such as text decoding, parsing JSON and detecting errors."""

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
        """Creates a new body option.

        Parameters:
            json: function to parse JSON from the HTTP response body. The default is to rely on the behaviour of the HTTP client library.
            text: function to decode text from the HTTP response body. The default is to rely on the behaviour of the HTTP client library.
            error: function to detect an error in the HTTP response. The default is to do nothing.
        """
        self.json = json
        self.text = text
        self.error = error

    def __call__(
        self,
        descriptor: Union[EndpointDescriptor[PT, T], AsyncEndpointDescriptor[PT, T]],
    ) -> None:
        """Apply the body option to the endpoint descriptor."""
        descriptor.get_text = self.text
        descriptor.get_json = self.json
        descriptor.get_error = self.error


body = BodyOption
