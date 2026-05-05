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


async def worker_loop() -> None:
    """Process jobs from the queue forever. Run as an asyncio task."""
    logger.info("Worker started")
    while True:
        func, args, kwargs = await _queue.get()
        name = getattr(func, "__name__", repr(func))
        try:
            logger.info("Running job: %s", name)
            await func(*args, **kwargs)
            logger.info("Completed job: %s", name)
        except Exception:
            logger.exception("Job failed: %s", name)
        finally:
            _queue.task_done()
