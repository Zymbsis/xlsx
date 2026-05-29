from typing import Annotated

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import SettingsDep

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(
    settings: SettingsDep, api_key: Annotated[str, Security(api_key_header)]
):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Unauthorized")
