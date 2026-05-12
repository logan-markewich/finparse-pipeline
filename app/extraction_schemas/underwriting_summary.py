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


class UnderwritingSummary(BaseModel):
    """Cross-document underwriting summary extracted from combined financial data."""

    borrower_name: str = Field(description="Primary borrower name as determined from the documents")
    verified_monthly_income: float = Field(
        description=(
            "Verified gross monthly income in USD. "
            "Calculate from pay stub base salary and pay frequency. "
            "Exclude overtime or one-time bonuses — note them separately in "
            "discrepancies if significant."
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
    total_monthly_obligations: float = Field(
        description=(
            "Total mandatory monthly obligations found on pay stubs in USD — "
            "includes child support, wage garnishments, IRS levies, and similar "
            "court-ordered or government withholdings. Exclude normal taxes and "
            "voluntary deductions."
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
            "Any discrepancies or red flags found across documents. Check for: "
            "name mismatches between documents, address mismatches, "
            "wage garnishments or court-ordered withholdings (indicate undisclosed debt), "
            "IRS tax levies or child support (mandatory obligations that affect DTI), "
            "asset balances or large deposits that seem inconsistent with stated income, "
            "heavy concentration in a single security, "
            "income that doesn't annualize cleanly (may indicate recent job/rate change), "
            "and any other unusual patterns."
        ),
    )
    notes: str = Field(
        default="",
        description="Any other observations relevant to loan underwriting",
    )
