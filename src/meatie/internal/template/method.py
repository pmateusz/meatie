#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import re
from typing import get_args

from meatie import Method

_method_pattern_pairs = [
    (method, re.compile("^" + method, re.IGNORECASE)) for method in get_args(Method)
]


def get_method(name: str, default: Method = "GET") -> Method:
    for method, pattern in _method_pattern_pairs:
        if re.match(pattern, name):
            return method
    return default
