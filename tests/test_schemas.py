"""Sanity checks that extraction schemas are valid and produce JSON schema."""

from app.extraction_schemas.brokerage_statement import BrokerageStatement
from app.extraction_schemas.pay_stub import PayStub
from app.extraction_schemas.underwriting_summary import UnderwritingSummary


def test_pay_stub_schema():
    schema = PayStub.model_json_schema()
    assert "properties" in schema
    assert "gross_pay" in schema["properties"]
    assert "deductions" in schema["properties"]


def test_brokerage_statement_schema():
    schema = BrokerageStatement.model_json_schema()
    assert "properties" in schema
    assert "accounts" in schema["properties"]


def test_underwriting_summary_schema():
    schema = UnderwritingSummary.model_json_schema()
    assert "properties" in schema
    assert "verified_monthly_income" in schema["properties"]
    assert "discrepancies" in schema["properties"]
    assert "months_of_reserves" in schema["properties"]
