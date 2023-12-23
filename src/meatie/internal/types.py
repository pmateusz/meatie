#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
from typing import TypeVar

from typing_extensions import ParamSpec

VT = TypeVar("VT")
T = TypeVar("T")
T_In = TypeVar("T_In", contravariant=True)
T_Out = TypeVar("T_Out", covariant=True)
PT = ParamSpec("PT")
