#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from typing import Any, Callable, Optional, get_args

from typing_extensions import Self

__all__ = ["api_ref", "ApiReference"]


class ApiReference:
    __slots__ = ("name", "fmt")

    def __init__(
        self, name: Optional[str] = None, fmt: Optional[Callable[[Any], Any]] = None
    ) -> None:
        """
        Customize handling of a parameter in the HTTP request.

        :param name: name of the query parameter in the HTTP request, if not set the name of the Python parameter is
         used by default
        :param fmt: conversion function to apply on the parameter value before sending the HTTP request
        """

        self.name = name
        self.fmt = fmt

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        # Python interpreter seems to reuse annotations, for that reason we also need to include the formatter
        if isinstance(other, ApiReference):
            return self.name == other.name and self.fmt == other.fmt
        return False

    @classmethod
    def from_signature(cls, parameter: inspect.Parameter) -> Self:
        for arg in get_args(parameter.annotation):
            if isinstance(arg, cls):
                if arg.name is None:
                    return cls(name=parameter.name, fmt=arg.fmt)
                return arg
        return cls(name=parameter.name, fmt=None)


api_ref = ApiReference
