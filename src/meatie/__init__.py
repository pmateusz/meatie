#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# isort:skip_file
import importlib.metadata
from .types import Request, Response, AsyncResponse, Method, Duration, Time, INF, MINUTE, HOUR, DAY
from .api_reference import api_ref
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
from .descriptor import EndpointDescriptor, Context
from .aio import BaseAsyncClient, AsyncEndpointDescriptor, AsyncContext
from .option import (
    limit,
    cache,
    retry,
    private,
    body,
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
    "Response",
    "AsyncResponse",
    "api_ref",
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
    "BaseClient",
    "Context",
    "EndpointDescriptor",
    "BaseAsyncClient",
    "AsyncEndpointDescriptor",
    "AsyncContext",
    "retry",
    "limit",
    "cache",
    "private",
    "body",
    "endpoint",
]

__version__ = importlib.metadata.version("meatie")
