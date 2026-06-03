import logging
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection
from groq import AsyncGroq

from app.config import settings
from app.exceptions.http import AppHTTPError

logger = logging.getLogger(__name__)


async def initialize(app: FastAPI) -> None:
    app.state.groq = AsyncGroq(api_key=settings.groq_api_key)
    logger.info("Groq client initialized")


async def shutdown(app: FastAPI) -> None:
    groq_client: AsyncGroq | None = getattr(app.state, "groq", None)

    if groq_client is not None:
        await groq_client.close()
        logger.info("Groq client shut down")


def get_groq_client(conn: HTTPConnection) -> AsyncGroq:
    groq_client: AsyncGroq | None = getattr(conn.app.state, "groq", None)

    if groq_client is None:
        raise AppHTTPError.service_unavailable("Groq client is not initialized")

    return groq_client


GroqClientDep = Annotated[AsyncGroq, Depends(get_groq_client)]
