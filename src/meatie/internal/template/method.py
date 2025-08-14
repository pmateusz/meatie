#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import re
from typing import get_args

from meatie.types import Method

__all__ = ["get_method"]

_method_pattern_pairs = [(method, re.compile("^" + method, re.IGNORECASE)) for method in get_args(Method)]


def get_method(name: str, default: Method = "GET") -> Method:
    """Extracts the HTTP method from the suffix.

    Returns:
        The HTTP method extracted from the suffix or the default method if the suffix does not match any known method.
    """
    for method, pattern in _method_pattern_pairs:
        if re.match(pattern, name):
            return method
    return default
