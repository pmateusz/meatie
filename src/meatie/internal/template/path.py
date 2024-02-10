#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import re
from typing import (
    Any,
)

from typing_extensions import Self

_param_pattern = re.compile(r"{(?P<name>[a-zA-Z_]\w*?)}")


class PathTemplate:
    __slots__ = ("template", "parameters")

    def __init__(self, template: str, parameters: list[str]) -> None:
        self.template = template
        self.parameters = parameters

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PathTemplate):
            return self.template == other.template and self.parameters == other.parameters
        if isinstance(other, str):
            return self.template == other
        return False

    def __hash__(self) -> int:
        return hash(self.template)

    def __contains__(self, item: str) -> bool:
        return item in self.parameters

    def __str__(self) -> str:
        return self.template

    def format(self, **kwargs: dict[str, Any]) -> str:
        return self.template.format(**kwargs)

    @classmethod
    def from_string(cls, template: str) -> Self:
        parameters = [match.group("name") for match in _param_pattern.finditer(template)]
        return cls(template, parameters)
