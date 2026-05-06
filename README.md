# FinParse Pipeline

A hands-on workshop where you build a financial document parsing, extraction, and review pipeline from scratch. You'll take real, intentionally difficult financial documents and turn them into structured, usable data using [LlamaParse](https://developers.llamaindex.ai/) and LLM-powered analysis.

## What You're Building

A loan underwriting pipeline that processes a borrower's financial documents:

1. **Parse** -- Upload a PDF (pay stub, brokerage statement), parse it into markdown using LlamaParse's agentic tier
2. **Extract** -- Pull structured fields from the parsed document using Pydantic schemas (employer name, gross pay, holdings, account values, etc.)
3. **Analyze** -- Feed extractions from multiple documents into an LLM to produce a cross-document underwriting summary with discrepancy flags
4. **Review** -- Human reviewer sees the AI analysis, approves or rejects with notes

## Target Documents

| Document | What makes it hard | Key extracted fields |
| --- | --- | --- |
| **Pay stub** (PDF) | Wildly varying layouts across payroll providers; mix of tables, grids, and free-form text | Employer name, employee name, gross/net pay, pay period, YTD gross income, deductions |
| **Brokerage statement** (PDF) | Multi-page with complex tables for holdings, transactions, gains/losses; varies by institution | Account holder, account number, statement period, total value, holdings, cash balance, gains/losses |

## Quick Start

```bash
# Clone and install
git clone <repo-url> && cd finparse-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env -- add your LLAMA_CLOUD_API_KEY and an LLM API key

# Run
fastapi dev app/main.py
```

Open http://localhost:8000/docs for the Swagger UI.

### Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `LLAMA_CLOUD_API_KEY` | Yes | Your LlamaCloud API key (`llx-...`) |
| `LLM_MODEL` | No | Any [litellm](https://docs.litellm.ai/docs/providers)-compatible model string. Default: `openai/gpt-4o` |
| `OPENAI_API_KEY` | Depends | Required if using an OpenAI model |
| `ANTHROPIC_API_KEY` | Depends | Required if using an Anthropic model |
| `DATABASE_URL` | No | SQLAlchemy async URL. Default: `sqlite+aiosqlite:///./finparse.db` |

## Project Structure

```
finparse-pipeline/
├── app/
│   ├── main.py                           # FastAPI app, lifespan (DB init + worker)
│   ├── config.py                         # pydantic-settings, reads from .env
│   ├── db.py                             # Async SQLAlchemy engine + session factory
│   ├── models.py                         # ORM models: Document, Extraction, Review
│   ├── schemas.py                        # Pydantic request/response schemas
│   ├── worker.py                         # In-process async job queue
│   ├── extraction_schemas/
│   │   ├── pay_stub.py                   # PayStubExtraction Pydantic model
│   │   └── brokerage_statement.py        # BrokerageStatementExtraction Pydantic model
│   ├── services/
│   │   ├── llm.py                        # litellm wrapper (provider-agnostic)
│   │   ├── documents.py                  # Document CRUD (upload, list, get)
│   │   ├── extractions.py               # Extraction CRUD (create, list, get)
│   │   ├── parser.py                     # TODO -- LlamaParse integration
│   │   ├── extractor.py                  # TODO -- Structured extraction
│   │   ├── llm_analysis.py              # TODO -- Cross-document LLM analysis
│   │   └── reviewer.py                  # TODO -- Review lifecycle + LLM analysis
│   └── routes/
│       ├── documents.py                  # /documents endpoints
│       ├── extractions.py               # /extractions endpoints
│       └── reviews.py                   # /reviews endpoints
├── documents/                            # Sample financial PDFs
├── tests/                                # Pytest test suite
├── pyproject.toml
└── .env.example
```

## What's Already Built

Everything except the four core services. The scaffolding is fully functional -- routes, database, job queue, schemas, tests -- so you can focus on the interesting parts.

### API Endpoints

All endpoints are live and wired up. They return proper errors until you implement the backing services.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/documents/upload` | Upload a PDF, creates a document record, enqueues parsing |
| `GET` | `/documents/` | List all documents |
| `GET` | `/documents/{id}` | Get document detail (includes parsed markdown) |
| `POST` | `/extractions/documents/{id}/extract` | Start extraction with a schema (`pay_stub` or `brokerage_statement`) |
| `GET` | `/extractions/{id}` | Get extraction result |
| `GET` | `/extractions/documents/{id}` | List all extractions for a document |
| `POST` | `/reviews/` | Create a review from completed extractions, enqueues LLM analysis |
| `GET` | `/reviews/{id}` | Get review (includes LLM summary) |
| `PATCH` | `/reviews/{id}` | Approve or reject a review |
| `GET` | `/reviews/` | List all reviews |

### Database Models

Three main models in `app/models.py`, with status tracking for async jobs:

- **Document** -- uploaded file, parsed markdown, status (`pending` -> `processing` -> `completed`/`failed`)
- **Extraction** -- structured data extracted from a document, linked to a schema name
- **Review** -- groups extractions for cross-document analysis, status (`pending` -> `analyzing` -> `ready_for_review` -> `approved`/`rejected`)

### Async Job Queue

LlamaParse operations are async (submit job, poll for results). Rather than blocking HTTP requests, the app uses an in-process async job queue (`app/worker.py`):

```
Upload PDF --> Route creates DB record --> Enqueues parse job --> Returns immediately
                                                  |
                                          Worker picks up job
                                                  |
                                          Calls LlamaParse API
                                                  |
                                          Updates DB on completion
```

The client polls `GET /documents/{id}` until `status` changes from `processing` to `completed`. Same pattern for extractions and reviews.

In production, you'd swap this for Celery/ARQ + Redis. The in-process queue keeps workshop setup to zero external dependencies.

### Extraction Schemas

Two Pydantic models define what to extract from each document type. These are pre-built in `app/extraction_schemas/`:

**PayStubExtraction** -- employer name, employee name, pay period, gross/net pay, YTD income, deductions breakdown

**BrokerageStatementExtraction** -- account holder, masked account number, statement period, total value, holdings (symbol/shares/value), cash balance, realized/unrealized gains

### LLM Wrapper

`app/services/llm.py` provides a thin `chat_completion()` function backed by [litellm](https://docs.litellm.ai/). Change the `LLM_MODEL` env var to use any provider (OpenAI, Anthropic, etc.) with no code changes.

## What You'll Implement

Four service files, each with a `TODO` stub and step-by-step instructions in the docstring.

### 1. `app/services/parser.py` -- Document Parsing

Implement `parse_document()`:
- Initialize the LlamaCloud client with your API key
- Upload the file and create a parsing job (agentic tier)
- Poll until the job completes
- Store the parsed markdown on the document record

### 2. `app/services/extractor.py` -- Structured Extraction

Implement `extract_from_document()`:
- Look up the Pydantic schema from the registry (`EXTRACTION_SCHEMAS`)
- Submit an extraction job to LlamaParse with the schema
- Poll for completion
- Store the structured JSON result

### 3. `app/services/llm_analysis.py` -- Cross-Document Analysis

Implement `analyze_extractions()`:
- Format extraction data from multiple documents into an LLM prompt
- Call `chat_completion()` with the provided system prompt (`ANALYSIS_SYSTEM_PROMPT`)
- Parse the JSON response into a structured underwriting summary
- The summary includes: verified income, liquid assets, months of reserves, and flagged discrepancies

### 4. `app/services/reviewer.py` -- Review Lifecycle

Implement two functions:

`run_review_analysis()` (background job):
- Load linked extractions from the database
- Call `analyze_extractions()` with the extracted data
- Store the LLM summary on the review record
- Update status to `ready_for_review`

`update_review()` (finish the TODO at the bottom):
- Set the reviewer's decision (approved/rejected)
- Store reviewer notes
- Update the review status

## End-to-End Flow

Once all four services are implemented, the full workflow looks like this:

```bash
# 1. Upload a pay stub
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@documents/pay_stub.pdf"
# Returns: {"id": 1, "status": "pending", ...}

# 2. Poll until parsed
curl http://localhost:8000/documents/1
# Returns: {"id": 1, "status": "completed", "parsed_markdown": "...", ...}

# 3. Extract structured data
curl -X POST http://localhost:8000/extractions/documents/1/extract \
  -H "Content-Type: application/json" \
  -d '{"schema_name": "pay_stub"}'
# Returns: {"id": 1, "status": "pending", ...}

# 4. Poll until extracted
curl http://localhost:8000/extractions/1
# Returns: {"id": 1, "status": "completed", "extracted_data": {...}, ...}

# 5. Repeat steps 1-4 for a brokerage statement (document 2, extraction 2)

# 6. Create a review from both extractions
curl -X POST http://localhost:8000/reviews/ \
  -H "Content-Type: application/json" \
  -d '{"extraction_ids": [1, 2]}'
# Returns: {"id": 1, "status": "pending", ...}

# 7. Poll until analysis is ready
curl http://localhost:8000/reviews/1
# Returns: {"id": 1, "status": "ready_for_review", "llm_summary": {...}, ...}

# 8. Approve or reject
curl -X PATCH http://localhost:8000/reviews/1 \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "reviewer_notes": "Income and assets verified"}'
```

Or just use the Swagger UI at http://localhost:8000/docs -- it's much easier.

## Development

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
ty check

# Test
pytest -v
```

## Architecture Notes

**Services own the DB lifecycle.** Routes are thin dispatchers -- they parse the request, call a service, and translate errors to HTTP responses. Each service function opens its own database session via `db.async_session()`, does its work, and commits. This avoids holding connections for the lifetime of an HTTP request and keeps business logic testable independently of FastAPI.

**In-process job queue over Celery.** For a workshop, the operational overhead of Redis + a separate worker process isn't worth the setup time. The `asyncio.Queue`-based worker in `app/worker.py` teaches the same pattern (enqueue, worker picks up, updates DB) without external dependencies.

**litellm for LLM calls.** Attendees bring whatever API key they have. Changing providers is a one-line `.env` change, not a code change.
