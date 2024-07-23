#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import inspect
from typing import Any, get_args

from typing_extensions import Callable, Self

__all__ = ["fmt", "Formatter"]


class Formatter:
    __slots__ = ("formatter",)

    def __init__(self, formatter: Callable[[Any], Any]) -> None:
        self.formatter = formatter

    def __call__(self, value: Any) -> Any:
        return self.formatter(value)

    def __hash__(self) -> int:
        return hash(self.formatter)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Formatter):
            return self.formatter == other.formatter
        return False

    @classmethod
    def from_signature(cls, parameter: inspect.Parameter) -> Self | None:
        for arg in get_args(parameter.annotation):
            if isinstance(arg, cls):
                return arg
        return None


fmt = Formatter
