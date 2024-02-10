#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from dataclasses import dataclass
from typing import Any, Optional, Union

from typing_extensions import Literal

Method = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]

Duration = float
Time = float

MINUTE = 60
HOUR = 3600
DAY = 86400

INF = float("inf")


@dataclass()
class Request:
    method: Method
    path: str
    params: dict[str, Union[str, int]]
    headers: dict[str, Union[str, bytes]]
    data: Optional[Union[str, bytes]] = None
    json: Any = None
