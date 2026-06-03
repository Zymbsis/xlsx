import logging
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection
from groq import AsyncGroq

from app.config import settings
from app.core.log_messages import GROQ_CONNECTED, GROQ_DISCONNECTED
from app.exceptions.http import AppHTTPError
from app.exceptions.messages import GROQ_NOT_INITIALIZED

logger = logging.getLogger(__name__)


async def connect(app: FastAPI) -> None:
    app.state.groq = AsyncGroq(api_key=settings.groq_api_key)
    logger.info(GROQ_CONNECTED)


async def disconnect(app: FastAPI) -> None:
    groq_client: AsyncGroq | None = getattr(app.state, "groq", None)

    if groq_client is not None:
        await groq_client.close()
        logger.info(GROQ_DISCONNECTED)


def get_groq_client(conn: HTTPConnection) -> AsyncGroq:
    groq_client: AsyncGroq | None = getattr(conn.app.state, "groq", None)

    if groq_client is None:
        raise AppHTTPError.service_unavailable(GROQ_NOT_INITIALIZED)

    return groq_client


GroqClientDep = Annotated[AsyncGroq, Depends(get_groq_client)]
