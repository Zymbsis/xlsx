import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.log_messages import APPLICATION_STARTUP_COMPLETE
from app.core.logging import setup_logging
from app.db import engine as pg
from app.db import redis
from app.llm import groq
from app.routers import ws, xlsx

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(settings.environment)

    await pg.connect()
    await redis.connect(app)
    await groq.connect(app)

    logger.info(APPLICATION_STARTUP_COMPLETE)

    yield
    await groq.disconnect(app)
    await redis.disconnect(app)
    await pg.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(xlsx.router)
app.include_router(ws.router)
