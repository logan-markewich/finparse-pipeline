from pydantic import BaseModel, Field


class Holding(BaseModel):
    symbol: str = Field(description="Ticker symbol or fund name")
    shares: float = Field(description="Number of shares held")
    market_value: float = Field(description="Current market value in USD")


class BrokerageStatementExtraction(BaseModel):
    """Structured extraction schema for a brokerage / investment account statement."""

    account_holder: str = Field(description="Name of the account holder")
    account_number_masked: str = Field(
        description="Account number, masked except last 4 digits (e.g. ****1234)"
    )
    statement_period_start: str = Field(description="Statement period start date (YYYY-MM-DD)")
    statement_period_end: str = Field(description="Statement period end date (YYYY-MM-DD)")
    total_account_value: float = Field(description="Total account value at end of period")
    holdings: list[Holding] = Field(
        default_factory=list,
        description="List of holdings / positions in the account",
    )
    cash_balance: float = Field(description="Cash / money market balance in the account")
    realized_gains: float | None = Field(
        default=None, description="Realized gains/losses for the period, if reported"
    )
    unrealized_gains: float | None = Field(
        default=None, description="Unrealized gains/losses, if reported"
    )
