"""Cross-document LLM analysis for underwriting review.

After structured data is extracted from multiple documents (pay stubs,
brokerage statements), this service feeds them into an LLM to produce
an underwriting summary — verified income, total liquid assets, months
of reserves, and flagged discrepancies.
"""

ANALYSIS_SYSTEM_PROMPT = """\
You are a loan underwriting assistant. You will be given structured data \
extracted from a borrower's financial documents (pay stubs, brokerage \
statements, etc.).

Analyze the documents and produce a JSON underwriting summary with the following fields:

{
    "borrower_name": "Name from the documents",
    "verified_monthly_income": 0.00,
    "verified_annual_income": 0.00,
    "total_liquid_assets": 0.00,
    "months_of_reserves": 0.0,
    "income_sources": [
        {"source": "employer name", "gross_monthly": 0.00, "document": "pay_stub"}
    ],
    "asset_summary": [
        {"account": "description", "value": 0.00, "document": "brokerage_statement"}
    ],
    "discrepancies": [
        {"description": "What doesn't match", "severity": "high/medium/low"}
    ],
    "notes": "Any other observations relevant to underwriting"
}

Rules:
- Calculate monthly income from pay stub data \
(use gross pay and pay period to annualize, then divide by 12)
- Total liquid assets = sum of all brokerage account values + cash balances
- Months of reserves = total liquid assets / verified monthly income
- Flag any discrepancies between documents (name mismatches, income inconsistencies)
- Flag anything unusual (very high deductions, negative cash balances)
- Be precise with numbers — do not round unless necessary
- Return ONLY the JSON object, no other text
"""


async def analyze_extractions(extractions_data: list[dict]) -> dict:
    """Run cross-document LLM analysis on extracted financial data.

    Args:
        extractions_data: List of dicts, each with "schema_name" and "data" keys.

    Returns:
        Structured underwriting summary as a dict.

    Steps to implement:
        1. Format the extraction data into a user message
        2. Call the LLM with the analysis system prompt
        3. Parse the JSON response
        4. Return the summary dict
    """
    # ------------------------------------------------------------------
    # TODO: Implement LLM analysis here
    #
    # 1. Build a user message that includes all extraction data
    # 2. Call chat_completion() with the system prompt and user message
    #    (from app.services.llm import chat_completion)
    # 3. Parse the JSON response from the LLM (json.loads)
    # 4. Return the parsed dict
    #
    # Hint: Use ANALYSIS_SYSTEM_PROMPT as the system message
    # ------------------------------------------------------------------
    raise NotImplementedError("Implement LLM analysis — see instructions above")
