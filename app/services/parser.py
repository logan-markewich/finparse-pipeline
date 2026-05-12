"""Document parsing service using LlamaParse.

This is the first service attendees implement. It handles:
1. Submitting a document to LlamaParse (agentic tier)
2. Polling for completion
3. Storing the parsed markdown in the database
"""

import asyncio

from llama_cloud import AsyncLlamaCloud

from app import db
from app.config import settings
from app.models import Document, JobStatus


async def parse_document(document_id: int, file_path: str) -> None:
    """Parse a document using LlamaParse and store the resulting markdown.

    This function runs as a background job (called via the worker queue).

    Steps to implement:
        1. Open a DB session and set the document status to "processing"
        2. Create a LlamaParse job using the async API:
            - Use the llama_cloud client (see: llama_cloud.client.LlamaCloud)
            - Upload the file to create a parsing job
            - Poll the job status until it completes
            - Retrieve the parsed markdown result
        3. Store the parsed markdown on the Document record
        4. Set status to "completed" (or "failed" on error)

    Hints:
        - from app.config import settings  # for settings.llama_cloud_api_key
        - The LlamaCloud client has methods for creating and polling parse jobs
        - Use `async with db.async_session() as session:` to get a DB session
        - Don't forget to await session.commit() after updating the document
    """
    async with db.async_session() as session:
        doc = await session.get(Document, document_id)
        if not doc:
            return

        doc.status = JobStatus.processing
        await session.commit()

    try:
        # 1. Initialize the LlamaCloud client with your API key
        client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)

        # 2. Upload the file and create a parsing job (use agentic tier)
        file_obj = await client.files.create(file=file_path, purpose="parse")
        job = await client.parsing.create(
            file_id=file_obj.id,
            tier="agentic",
            version="latest",
        )

        # 3. Poll until the job is complete
        result = await client.parsing.get(job.id, expand=["markdown_full"])
        while result.job.status not in ["COMPLETED", "FAILED", "CANCELED"]:
            await asyncio.sleep(5)  # wait before polling again
            result = await client.parsing.get(job.id, expand=["markdown_full"])

        if result.job.status != "COMPLETED":
            raise Exception(
                f"Parsing job failed: {result.job.status} -> {result.job.error_message}"
            )

        # 4. Get the parsed markdown result
        parsed_markdown = result.markdown_full
        if not parsed_markdown:
            raise Exception("Parsed markdown is empty!")

        # 5. Store it on doc.parsed_markdown
        async with db.async_session() as session:
            doc = await session.get(Document, document_id)
            doc.parsed_markdown = parsed_markdown
            doc.status = JobStatus.completed
            await session.commit()
    
    except Exception as e:
        async with db.async_session() as session:
            doc = await session.get(Document, document_id)
            if doc:
                doc.status = JobStatus.failed
                doc.error = str(e)
                await session.commit()
        raise
