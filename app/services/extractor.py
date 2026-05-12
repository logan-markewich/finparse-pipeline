"""Structured extraction service using LlamaParse.

After a document is parsed, this service runs structured extraction
against it using a Pydantic schema to pull out specific fields.
"""

import asyncio
from llama_cloud import AsyncLlamaCloud

from app import db
from app.config import settings
from app.extraction_schemas.brokerage_statement import BrokerageStatement
from app.extraction_schemas.pay_stub import PayStub
from app.extraction_schemas.underwriting_summary import UnderwritingSummary
from app.models import Document, Extraction, JobStatus

# Registry mapping schema names to Pydantic models
EXTRACTION_SCHEMAS: dict = {
    "pay_stub": PayStub,
    "brokerage_statement": BrokerageStatement,
    "underwriting_summary": UnderwritingSummary,
}


async def extract_from_document(extraction_id: int, document_id: int, schema_name: str) -> None:
    """Run structured extraction on a parsed document.

    This function runs as a background job (called via the worker queue).

    Steps to implement:
        1. Look up the schema class from EXTRACTION_SCHEMAS
        2. Set the extraction status to "processing"
        3. Use LlamaParse's extraction API:
            - Submit an extraction job with the document and schema
            - Poll for completion
            - Get the structured result
        4. Store the result as JSON in extraction.extracted_data
        5. Set status to "completed" (or "failed" on error)

    Hints:
        - The schema Pydantic model can be converted to JSON Schema for the API
        - Use schema_class.model_json_schema() to get the JSON schema
        - Store the result with json.dumps()
    """
    if schema_name not in EXTRACTION_SCHEMAS:
        async with db.async_session() as session:
            extraction = await session.get(Extraction, extraction_id)
            if extraction:
                extraction.status = JobStatus.failed
                available = list(EXTRACTION_SCHEMAS.keys())
                extraction.error = f"Unknown schema: {schema_name}. Available: {available}"
                await session.commit()
        return

    _schema_class = EXTRACTION_SCHEMAS[schema_name]

    async with db.async_session() as session:
        extraction = await session.get(Extraction, extraction_id)
        if not extraction:
            return

        extraction.status = JobStatus.processing
        await session.commit()

    try:
        # 1. Initialize the LlamaCloud client with your API key
        client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)

        # 2. Get the document record to find the file path
        file_path = None
        async with db.async_session() as session:
            extraction = await session.get(Extraction, extraction_id)
            if not extraction:
                return
            
            document = await session.get(Document, extraction.document_id)
            if not document:
                raise Exception("Document not found for extraction")
            
            file_path = document.file_path
        
        if not file_path:
            raise Exception("Document file path is missing")

        # 3. Submit an extraction job with the Pydantic schema
        file_obj = await client.files.create(file=file_path, purpose="extract")
        job = await client.extract.create(
            file_input=file_obj.id,
            configuration={
                "data_schema": _schema_class.model_json_schema(),
                "tier": "agentic",
            }
        )

        # 4. Poll until the job is complete
        result = await client.extract.get(job.id)
        while result.status not in ["COMPLETED", "FAILED", "CANCELED"]:
            await asyncio.sleep(5)  # wait before polling again
            result = await client.extract.get(job.id)
        
        if result.status != "COMPLETED":
            raise Exception(
                f"Extraction job failed: {result.status} -> {result.error_message}"
            )
        
        # 5. Get the structured extraction result and validate it with the Pydantic model
        structured_result = _schema_class.model_validate(result.extract_result)

        # 6. Store it: extraction.extracted_data = json.dumps(result)
        async with db.async_session() as session:
            extraction = await session.get(Extraction, extraction_id)
            if not extraction:
                return
            extraction.extracted_data = structured_result.model_dump_json()
            extraction.status = JobStatus.completed
            await session.commit()

    except Exception as e:
        async with db.async_session() as session:
            extraction = await session.get(Extraction, extraction_id)
            if not extraction:
                return
            extraction.status = JobStatus.failed
            extraction.error = str(e)
            await session.commit()
            raise
