"""Sanity checks that extraction schemas are valid and produce JSON schema."""

from app.extraction_schemas.brokerage_statement import BrokerageStatementExtraction
from app.extraction_schemas.pay_stub import PayStubExtraction


def test_pay_stub_schema():
    schema = PayStubExtraction.model_json_schema()
    assert "properties" in schema
    assert "gross_pay" in schema["properties"]
    assert "deductions" in schema["properties"]


def test_brokerage_statement_schema():
    schema = BrokerageStatementExtraction.model_json_schema()
    assert "properties" in schema
    assert "holdings" in schema["properties"]
    assert "total_account_value" in schema["properties"]
