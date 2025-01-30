#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from enum import Enum
from typing import Any, Callable, Optional


class Kind(Enum):
    """Type of parameter in an HTTP request."""

    UNKNOWN = 0
    PATH = 1
    QUERY = 2
    BODY = 3


class Parameter:
    """Represents a parameter in an HTTP request. It could be either a path URL parameter, an HTTP query parameter, or the HTTP request body."""

    __slots__ = ("kind", "name", "api_ref", "default_value", "formatter", "marshaller")

    def __init__(
        self,
        kind: Kind,
        name: str,
        api_ref: str,
        default_value: Any = None,
        formatter: Optional[Callable[[Any], Any]] = None,
        marshaller: Optional[Callable[[Any], dict[str, Any]]] = None,  # TODO: replace marshaller by formatter
    ) -> None:
        """Creates a Parameter.

        Args:
            kind: type of parameter in an HTTP request.
            name: name used in the Python function.
            api_ref: name of the parameter used in the API.
            default_value: default value of the parameter.
            formatter: function to apply on the parameter value before sending the HTTP request.
            marshaller: function to apply on the parameter value before sending the HTTP request. In contrast to the formatter function, which produces a single value, the marshaller function returns a dictionary of key value pairs.
        """
        self.kind = kind
        self.name = name
        self.api_ref = api_ref
        self.default_value = default_value
        self.formatter = formatter
        self.marshaller = marshaller

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Parameter):
            return (
                self.name == other.name
                and self.kind == other.kind
                and self.api_ref == other.api_ref
                and self.default_value == other.default_value
            )
        return False
