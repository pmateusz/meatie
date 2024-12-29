import sys

import pytest

if sys.version_info < (3, 12):
    pytest.skip("requires Python 3.12", allow_module_level=True)
