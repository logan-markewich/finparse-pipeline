from pydantic import BaseModel, Field


class Deduction(BaseModel):
    name: str = Field(
        description="Name of the deduction (e.g. Federal Tax, 401k, Health Insurance)"
    )
    amount: float = Field(description="Deduction amount for the current pay period")


class PayStub(BaseModel):
    """Structured extraction schema for a pay stub document."""

    employer_name: str = Field(description="Name of the employer / company")
    employee_name: str = Field(description="Full name of the employee")
    pay_period_start: str = Field(description="Pay period start date (YYYY-MM-DD)")
    pay_period_end: str = Field(description="Pay period end date (YYYY-MM-DD)")
    gross_pay: float = Field(description="Gross pay for the current pay period")
    net_pay: float = Field(description="Net pay (take-home) for the current pay period")
    ytd_gross_income: float = Field(description="Year-to-date gross income")
    deductions: list[Deduction] = Field(
        default_factory=list,
        description="Breakdown of deductions for the current pay period",
    )
