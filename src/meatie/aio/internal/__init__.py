#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# isort:skip_file
from .adapter import TypeAdapter, JsonAdapter, get_adapter
from .request_template import RequestTemplate, ApiRef, PathTemplate
from .endpoint_descriptor import EndpointDescriptor, EndpointOption

__all__ = [
    "TypeAdapter",
    "JsonAdapter",
    "get_adapter",
    "RequestTemplate",
    "ApiRef",
    "PathTemplate",
    "EndpointDescriptor",
    "EndpointOption",
]
