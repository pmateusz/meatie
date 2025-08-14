#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""Internal package for building HTTP requests based on Python signatures."""

from .method import get_method
from .parameter import Kind, Parameter
from .path import PathTemplate
from .request import RequestTemplate

__all__ = ["Kind", "Parameter", "PathTemplate", "RequestTemplate", "get_method"]
