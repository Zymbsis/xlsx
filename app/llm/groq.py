from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.requests import HTTPConnection
from groq import AsyncGroq

from app.config import settings
from app.exceptions.http import AppHTTPError
from app.exceptions.messages import GROQ_NOT_INITIALIZED


async def connect(app: FastAPI) -> None:
    app.state.groq = AsyncGroq(api_key=settings.groq_api_key)


async def disconnect(app: FastAPI) -> None:
    groq_client: AsyncGroq | None = getattr(app.state, "groq", None)

    if groq_client is not None:
        await groq_client.close()


def get_groq_client(conn: HTTPConnection) -> AsyncGroq:
    groq_client: AsyncGroq | None = getattr(conn.app.state, "groq", None)

    if groq_client is None:
        raise AppHTTPError.service_unavailable(GROQ_NOT_INITIALIZED)

    return groq_client


GroqClientDep = Annotated[AsyncGroq, Depends(get_groq_client)]
