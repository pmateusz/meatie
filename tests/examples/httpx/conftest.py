import pytest

pytest.importorskip("httpx")
pytest.importorskip("pydantic", minversion="2.0.0")
