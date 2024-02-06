#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import TypeVar

from typing_extensions import ParamSpec

Duration = float
Time = float

MINUTE = 60
HOUR = 3600
DAY = 86400

INF = float("inf")

VT = TypeVar("VT")
T = TypeVar("T")
T_In = TypeVar("T_In", contravariant=True)
T_Out = TypeVar("T_Out", covariant=True)
PT = ParamSpec("PT")
RequestBodyType = TypeVar("RequestBodyType", contravariant=True)
ResponseBodyType = TypeVar("ResponseBodyType", covariant=True)
