#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# isort:skip_file
import importlib.metadata
from .types import Request, Method, Duration, Time, INF, MINUTE, HOUR, DAY
from .error import (
    MeatieError,
    RetryError,
    RequestError,
    RateLimitExceeded,
    TransportError,
    ProxyError,
    ServerError,
    Timeout,
    HttpStatusError,
    ResponseError,
    ParseResponseError,
)
from .internal.retry import (
    RetryContext,
    BaseCondition,
    Condition,
    after,
    after_attempt,
    always,
    never,
    has_status,
    has_exception_type,
    has_exception_cause_type,
    zero,
    uniform,
    exponential,
    fixed,
    jit,
)
from .internal.cache import Cache
from .internal.limit import Limiter, Rate
from .client import BaseClient
from .api_ref import ApiRef
from .descriptor import EndpointDescriptor, Context
from .option import (
    limit,
    cache,
    retry,
    private,
)
from .endpoint import endpoint

__all__ = [
    "Duration",
    "Time",
    "INF",
    "MINUTE",
    "HOUR",
    "DAY",
    "Method",
    "Request",
    "MeatieError",
    "RetryError",
    "RequestError",
    "RateLimitExceeded",
    "TransportError",
    "ProxyError",
    "ServerError",
    "Timeout",
    "HttpStatusError",
    "ResponseError",
    "ParseResponseError",
    "RetryContext",
    "BaseCondition",
    "Condition",
    "zero",
    "uniform",
    "exponential",
    "fixed",
    "jit",
    "never",
    "after",
    "after_attempt",
    "always",
    "has_status",
    "has_exception_type",
    "has_exception_cause_type",
    "Cache",
    "Limiter",
    "Rate",
    "ApiRef",
    "BaseClient",
    "Context",
    "EndpointDescriptor",
    "retry",
    "limit",
    "cache",
    "private",
    "endpoint",
]

__version__ = importlib.metadata.version("meatie")
