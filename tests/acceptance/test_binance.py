#  Copyright 2023 The Meatie Authors. All rights reserved.
#  Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

# mypy: disable-error-code="valid-type"

import hashlib
import hmac
import time
import urllib.parse
from decimal import Decimal
from typing import Any, Optional, Union

import pytest
from aiohttp import ClientSession
from meatie import HOUR, Limiter, Rate, Request, endpoint
from meatie.aio import (
    cache,
    limit,
    private,
)
from meatie_aiohttp import AiohttpClient

pydantic = pytest.importorskip("pydantic", minversion="2.0.0")
BaseModel: type = pydantic.BaseModel
Field = pydantic.Field
AnyHttpUrl = pydantic.AnyHttpUrl
pydantic_settings = pytest.importorskip("pydantic_settings")
BaseSettings: type = pydantic_settings.BaseSettings
SettingsConfigDict: type = pydantic_settings.SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="test_", env_file=".env", env_file_encoding="utf-8"
    )

    api_key: str = Field(alias="binance_api_key")
    secret: str = Field(alias="binance_secret")
    proxy: AnyHttpUrl = Field(alias="binance_proxy")


class Symbol(BaseModel):
    symbol: str
    status: str
    base_asset: str = Field(alias="baseAsset")
    base_asset_precision: int = Field(alias="baseAssetPrecision")
    quote_asset: str = Field(alias="quoteAsset")
    quote_asset_precision: int = Field(alias="quoteAssetPrecision")
    base_commission_precision: int = Field(alias="baseCommissionPrecision")
    quote_commission_precision: int = Field(alias="quoteCommissionPrecision")


class RateLimit(BaseModel):
    interval: str
    interval_num: int = Field(alias="intervalNum")
    limit: int
    rate_limit_type: str = Field(alias="rateLimitType")


class ExchangeInfo(BaseModel):
    timezone: str
    server_time: int = Field(alias="serverTime")
    rate_limits: list[RateLimit] = Field(alias="rateLimits")
    exchange_filters: list[Any] = Field(alias="exchangeFilters")
    symbols: list[Symbol]


class AssetWalletBalance(BaseModel):
    activate: bool
    balance: Decimal
    wallet_name: str = Field(alias="walletName")


@pytest.fixture(name="settings")
def settings_fixture() -> Settings:
    try:
        return Settings()
    except ValueError:
        pytest.skip("Failed to load settings")


class Binance(AiohttpClient):
    def __init__(
        self,
        proxy: Optional[Union[AnyHttpUrl, str]] = None,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> None:
        session_params = {}
        if proxy is not None:
            session_params["proxy"] = str(proxy)

        super().__init__(
            ClientSession(base_url="https://api.binance.com"),
            session_params=session_params,
            limiter=Limiter(rate=Rate(tokens_per_sec=1), capacity=300),
        )

        self.api_key = api_key
        self.secret = secret

    async def authenticate(self, request: Request) -> None:
        if self.api_key is None:
            raise RuntimeError("'api_key' is None")

        if self.secret is None:
            raise RuntimeError("'secret' is None")

        timestamp = int(time.monotonic() * 1000) - 15000
        request.headers["X-MBX-APIKEY"] = self.api_key
        request.query_params["recvWindow"] = str(60000)
        request.query_params["timestamp"] = str(timestamp)

        query_params = urllib.parse.urlencode(request.query_params)
        raw_signature = hmac.new(
            self.secret.encode("utf-8"), query_params.encode("utf-8"), hashlib.sha256
        )
        signature = raw_signature.hexdigest()
        request.query_params["signature"] = signature

    @endpoint("/api/v3/exchangeInfo", cache(ttl=HOUR), limit(tokens=20))
    async def get_exchange_info(self) -> ExchangeInfo:
        ...

    @endpoint("/sapi/v1/asset/wallet/balance", private, limit(tokens=60))
    async def get_asset_wallet_balance(self) -> list[AssetWalletBalance]:
        ...


@pytest.mark.asyncio()
async def test_get_exchange_info(settings: Settings) -> None:
    # GIVEN-WHEN
    async with Binance() as api:
        result = await api.get_exchange_info()

    # THEN
    assert isinstance(result, ExchangeInfo)


@pytest.mark.asyncio()
async def test_get_spot_positions(settings: Settings) -> None:
    # GIVEN-WHEN
    async with Binance(
        proxy=settings.proxy, api_key=settings.api_key, secret=settings.secret
    ) as api:
        result = await api.get_asset_wallet_balance()

    # THEN
    assert result
