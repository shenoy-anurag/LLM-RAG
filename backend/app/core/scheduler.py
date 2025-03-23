from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from app.core.config import settings


aio_scheduler = AsyncIOScheduler(timezone=timezone(settings.TIME_ZONE))


@asynccontextmanager
async def lifespan(app: FastAPI):
    aio_scheduler.start()
    yield
    aio_scheduler.shutdown()
