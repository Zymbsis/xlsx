from typing import Annotated

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.config import SettingsDep
from app.exceptions.http import AppHTTPError

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(settings: SettingsDep, api_key: Annotated[str, Security(api_key_header)]) -> None:
    if api_key != settings.api_key:
        raise AppHTTPError.forbidden("Unauthorized")
