"""Simple async job queue that runs in-process alongside FastAPI.

Jobs are enqueued as async callables and executed sequentially by a background
worker loop. In production you'd swap this for Celery/ARQ + Redis, but for a
workshop this keeps the setup to zero external dependencies.
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

_queue: asyncio.Queue[tuple[Any, tuple, dict]] = asyncio.Queue()


async def enqueue(func: Any, *args: Any, **kwargs: Any) -> None:
    """Add an async job to the queue."""
    await _queue.put((func, args, kwargs))
    name = getattr(func, "__name__", repr(func))
    logger.info("Enqueued job: %s", name)


_MAX_CONCURRENT = 5


async def _run_job(sem: asyncio.Semaphore, func: Any, args: tuple, kwargs: dict) -> None:
    """Execute a single job under the concurrency semaphore."""
    name = getattr(func, "__name__", repr(func))
    async with sem:
        try:
            logger.info("Running job: %s", name)
            await func(*args, **kwargs)
            logger.info("Completed job: %s", name)
        except Exception:
            logger.exception("Job failed: %s", name)
        finally:
            _queue.task_done()


async def worker_loop() -> None:
    """Process jobs from the queue, running up to _MAX_CONCURRENT at once."""
    logger.info("Worker started (concurrency=%d)", _MAX_CONCURRENT)
    sem = asyncio.Semaphore(_MAX_CONCURRENT)
    while True:
        func, args, kwargs = await _queue.get()
        asyncio.create_task(_run_job(sem, func, args, kwargs))

