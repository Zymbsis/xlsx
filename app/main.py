from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import redis
from app.db.engine import engine
from app.routers import ws, xlsx


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.close()
    await redis.connect(app)
    yield
    await engine.dispose()
    await redis.disconnect(app)


app = FastAPI(lifespan=lifespan)

app.include_router(xlsx.router)
app.include_router(ws.router)
