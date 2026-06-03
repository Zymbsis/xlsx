import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.config import settings
from app.core.log_messages import POSTGRESQL_CONNECTED, POSTGRESQL_DISCONNECTED

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.pg_database_url, echo=settings.environment == "dev")
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


async def connect() -> None:
    async with engine.connect() as conn:
        await conn.close()
    logger.info(POSTGRESQL_CONNECTED)


async def disconnect() -> None:
    await engine.dispose()
    logger.info(POSTGRESQL_DISCONNECTED)
