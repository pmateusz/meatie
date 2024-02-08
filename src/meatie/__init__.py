#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# isort:skip_file
import importlib.metadata
from .internal.types import Duration, Time, INF, MINUTE, HOUR, DAY
from .internal import CacheStore, Limiter, Rate
from .types import (
    Request,
    Response,
    Method,
)
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
from .request_template import RequestTemplate, PathTemplate, ApiRef
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
    "Response",
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
    "RequestTemplate",
    "PathTemplate",
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
