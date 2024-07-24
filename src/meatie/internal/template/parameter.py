#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from enum import Enum
from typing import Any, Callable, Optional


class Kind(Enum):
    UNKNOWN = 0
    PATH = 1
    QUERY = 2
    BODY = 3


class Parameter:
    __slots__ = ("kind", "name", "api_ref", "default_value", "formatter")

    def __init__(
        self,
        kind: Kind,
        name: str,
        api_ref: str,
        default_value: Any = None,
        formatter: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.kind = kind
        self.name = name
        self.api_ref = api_ref
        self.default_value = default_value
        self.formatter = formatter

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
