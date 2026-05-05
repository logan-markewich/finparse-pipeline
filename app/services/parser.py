"""Document parsing service using LlamaParse.

This is the first service attendees implement. It handles:
1. Submitting a document to LlamaParse (agentic tier)
2. Polling for completion
3. Storing the parsed markdown in the database
"""

from app import db
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
            # ------------------------------------------------------------------
            # TODO: Implement LlamaParse integration here
            #
            # 1. Initialize the LlamaCloud client with your API key
            # 2. Upload the file and create a parsing job (use agentic tier)
            # 3. Poll until the job is complete
            # 4. Get the parsed markdown result
            # 5. Store it on doc.parsed_markdown
            # ------------------------------------------------------------------
            raise NotImplementedError("Implement LlamaParse integration — see instructions above")

            doc.status = JobStatus.completed
            await session.commit()

        except Exception as e:
            doc.status = JobStatus.failed
            doc.error = str(e)
            await session.commit()
            raise
