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
        self.name = name
        self.fmt = fmt

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ApiReference):
            return self.name == other.name
        return False

    @classmethod
    def from_signature(cls, parameter: inspect.Parameter) -> Self:
        for arg in get_args(parameter.annotation):
            if isinstance(arg, cls):
                if arg.name is None:
                    arg.name = parameter.name
                return arg
        return cls(name=parameter.name, fmt=None)


api_ref = ApiReference
