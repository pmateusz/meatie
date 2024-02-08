#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# isort:skip_file
import importlib.metadata
from .internal import CacheStore, Limiter, Rate
from .types import Request, Method, Duration, Time, INF, MINUTE, HOUR, DAY
from .error import (
    MeatieError,
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
from .client import BaseClient
from .api_ref import ApiRef
from .descriptor import EndpointDescriptor, Context
from .option import (
    Cache,
    Limit,
    Retry,
    WaitExponential,
    NoWait,
    NeverStop,
    RetryOnStatusCode,
    RetryOnTooManyRequestsStatus,
    RetryOnServerConnectionError,
    RetryOnExceptionType,
    StopAfter,
    Private,
)
from .endpoint import endpoint

__all__ = [
    "Duration",
    "Time",
    "INF",
    "MINUTE",
    "HOUR",
    "DAY",
    "Request",
    "MeatieError",
    "RequestError",
    "RateLimitExceeded",
    "TransportError",
    "ProxyError",
    "ServerError",
    "Timeout",
    "HttpStatusError",
    "ResponseError",
    "ParseResponseError",
    "Method",
    "CacheStore",
    "Limiter",
    "Rate",
    "ApiRef",
    "BaseClient",
    "Context",
    "EndpointDescriptor",
    "Cache",
    "Limit",
    "Retry",
    "WaitExponential",
    "NoWait",
    "NeverStop",
    "RetryOnStatusCode",
    "RetryOnTooManyRequestsStatus",
    "RetryOnServerConnectionError",
    "RetryOnExceptionType",
    "StopAfter",
    "Private",
    "endpoint",
]

__version__ = importlib.metadata.version("meatie")
