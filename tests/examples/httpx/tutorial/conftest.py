import sys

import pytest

if sys.version_info < (3, 11):
    pytest.skip("requires Python 3.11", allow_module_level=True)
