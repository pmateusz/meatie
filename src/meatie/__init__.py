#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""Meatie is a metaprogramming library for building HTTP REST API clients based on methods annotated with type hints."""

from .aio import AsyncContext, AsyncEndpointDescriptor, BaseAsyncClient
from .api_reference import api_ref
from .client import BaseClient
from .descriptor import Context, EndpointDescriptor
from .endpoint import endpoint
from .error import (
    HttpStatusError,
    MeatieError,
    ParseResponseError,
    ProxyError,
    RateLimitExceeded,
    RequestError,
    ResponseError,
    RetryError,
    ServerError,
    Timeout,
    TransportError,
)
from .internal.cache import Cache
from .internal.limit import Limiter, Rate
from .internal.retry import (
    BaseCondition,
    Condition,
    RetryContext,
    after,
    after_attempt,
    always,
    exponential,
    fixed,
    has_exception_cause_type,
    has_exception_type,
    has_status,
    jit,
    never,
    uniform,
    zero,
)
from .option import (
    body,
    cache,
    limit,
    private,
    retry,
)
from .types import (
    DAY,
    HOUR,
    INF,
    MINUTE,
    AsyncResponse,
    Duration,
    Method,
    Request,
    Response,
    Time,
)

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
