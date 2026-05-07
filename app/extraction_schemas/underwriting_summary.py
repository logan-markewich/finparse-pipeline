from pydantic import BaseModel, Field


class IncomeSource(BaseModel):
    source: str = Field(description="Employer or income source name")
    gross_monthly: float = Field(description="Gross monthly income from this source in USD")
    document_type: str = Field(description="Source document type (e.g. pay_stub)")


class AssetAccount(BaseModel):
    account: str = Field(description="Account description (e.g. Fidelity Brokerage)")
    value: float = Field(description="Total account value in USD")
    document_type: str = Field(description="Source document type (e.g. brokerage_statement)")


class Discrepancy(BaseModel):
    description: str = Field(description="What doesn't match across documents")
    severity: str = Field(description="high, medium, or low")


class UnderwritingSummaryExtraction(BaseModel):
    """Cross-document underwriting summary extracted from combined financial data."""

    borrower_name: str = Field(description="Primary borrower name as determined from the documents")
    verified_monthly_income: float = Field(
        description=(
            "Verified gross monthly income in USD. "
            "Calculate from pay stub gross pay and pay frequency."
        )
    )
    verified_annual_income: float = Field(
        description="Verified gross annual income in USD (monthly * 12)"
    )
    total_liquid_assets: float = Field(
        description=(
            "Total liquid assets in USD — sum of all brokerage account values and cash balances"
        )
    )
    months_of_reserves: float = Field(
        description="Total liquid assets divided by verified monthly income"
    )
    income_sources: list[IncomeSource] = Field(
        default_factory=list, description="Breakdown of all income sources"
    )
    asset_summary: list[AssetAccount] = Field(
        default_factory=list, description="Breakdown of all asset accounts"
    )
    discrepancies: list[Discrepancy] = Field(
        default_factory=list,
        description=(
            "Any discrepancies found across documents — name mismatches, "
            "income inconsistencies, unusual deductions, etc."
        ),
    )
    notes: str = Field(
        default="",
        description="Any other observations relevant to loan underwriting",
    )
