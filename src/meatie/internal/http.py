#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

Method = Literal["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]


@dataclass()
class Request:
    method: Method
    path: str
    query_params: dict[str, Union[str, int]]
    headers: dict[str, Union[str, bytes]]
    data: Optional[bytes] = None
    json: Any = None
