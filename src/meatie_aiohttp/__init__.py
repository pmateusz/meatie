#  Copyright 2024 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""Aiohttp client implementation for meatie."""

# isort:skip_file
from .response import Response
from .client import Client

__all__ = ["Response", "Client"]
