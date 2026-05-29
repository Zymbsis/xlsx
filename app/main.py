from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.engine import engine
from app.routers import xlsx


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.close()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(xlsx.router)
