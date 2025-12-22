#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from typing import Any, Callable, Optional, get_args

from typing_extensions import Self

__all__ = ["api_ref", "ApiReference"]


class ApiReference:
    """ApiReference stores additional settings that customize handling of a parameter in the HTTP request."""

    __slots__ = ("name", "fmt", "unwrap")

    def __init__(
        self,
        name: Optional[str] = None,
        fmt: Optional[Callable[[Any], Any]] = None,
        unwrap: Optional[Callable[[Any], dict[str, Any]]] = None,
    ) -> None:
        """Create an ApiReference.

        Args:
            name: the name of the query parameter in the HTTP request, the name of the Python parameter is used as default.
            fmt: conversion function to apply on the parameter value before sending the HTTP request
            unwrap: conversion function to apply on the parameter value before sending the HTTP request. In contrast to the fmt function, which produces a single value, the unwrap function returns a dictionary of key value pairs.
        """
        self.name = name
        self.fmt = fmt
        self.unwrap = unwrap

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        # Python interpreter seems to reuse annotations, for that reason we also need to include the formatter
        if isinstance(other, ApiReference):
            return self.name == other.name and self.fmt == other.fmt and self.unwrap == other.unwrap
        return False

    @classmethod
    def from_signature(cls, parameter: inspect.Parameter, resolved_annotation: Optional[Any] = None) -> Self:
        """Create an ApiReference from the Python method parameter.

        Args:
            parameter: The parameter from the function signature.
            resolved_annotation: The resolved type hint (from get_type_hints with include_extras=True).
                If provided, this is tried first, then falls back to parameter.annotation.
        """
        # Try resolved annotation first (handles stringified annotations from future imports)
        # If not found, fall back to parameter.annotation (handles local functions in tests)
        for annotation in [resolved_annotation, parameter.annotation]:
            if annotation is None:
                continue
            for arg in get_args(annotation):
                if isinstance(arg, cls):
                    if arg.name is None:
                        return cls(name=parameter.name, fmt=arg.fmt, unwrap=arg.unwrap)
                    return arg
        return cls(name=parameter.name, fmt=None, unwrap=None)


api_ref = ApiReference
