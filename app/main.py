import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import engine
from app.models import Base
from app.routes import documents, extractions, reviews
from app.worker import worker_loop

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background worker
    worker_task = asyncio.create_task(worker_loop())

    yield

    # Shutdown
    worker_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await worker_task


app = FastAPI(
    title="FinParse Pipeline",
    description="Parse, extract, and review financial documents",
    lifespan=lifespan,
)

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(extractions.router, prefix="/extractions", tags=["Extractions"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])


@app.get("/health")
async def health():
    return {"status": "ok"}
