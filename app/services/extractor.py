"""Structured extraction service using LlamaParse.

After a document is parsed, this service runs structured extraction
against it using a Pydantic schema to pull out specific fields.
"""

from app import db
from app.extraction_schemas.brokerage_statement import BrokerageStatementExtraction
from app.extraction_schemas.pay_stub import PayStubExtraction
from app.extraction_schemas.underwriting_summary import UnderwritingSummaryExtraction
from app.models import Extraction, JobStatus

# Registry mapping schema names to Pydantic models
EXTRACTION_SCHEMAS: dict = {
    "pay_stub": PayStubExtraction,
    "brokerage_statement": BrokerageStatementExtraction,
    "underwriting_summary": UnderwritingSummaryExtraction,
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
            # ------------------------------------------------------------------
            # TODO: Implement LlamaParse extraction here
            #
            # 1. Initialize the LlamaCloud client with your API key
            # 2. Get the document record to find the file path
            # 3. Submit an extraction job with the Pydantic schema
            # 4. Poll until the job is complete
            # 5. Get the structured extraction result
            # 6. Store it: extraction.extracted_data = json.dumps(result)
            # ------------------------------------------------------------------
            raise NotImplementedError("Implement LlamaParse extraction — see instructions above")

            extraction.status = JobStatus.completed
            await session.commit()

        except Exception as e:
            extraction.status = JobStatus.failed
            extraction.error = str(e)
            await session.commit()
            raise
