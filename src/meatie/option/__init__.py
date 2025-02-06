#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""Provides options for customizing the endpoint behaviour such as caching, rate limiting and retries."""

__all__ = ["cache", "limit", "private", "retry", "body"]

from .body_option import BodyOption
from .cache_option import CacheOption
from .limit_option import LimitOption
from .private_option import PrivateOption
from .retry_option import RetryOption

cache = CacheOption
limit = LimitOption
retry = RetryOption
body = BodyOption
private = PrivateOption()
