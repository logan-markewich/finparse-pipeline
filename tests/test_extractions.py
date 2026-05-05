async def test_extract_document_not_found(client):
    response = await client.post(
        "/extractions/documents/999/extract",
        json={"schema_name": "pay_stub"},
    )
    assert response.status_code == 404


async def test_extract_document_not_parsed(client):
    """Upload a doc (status=pending), then try to extract — should fail."""
    import io

    file = io.BytesIO(b"%PDF-1.4 fake")
    upload = await client.post(
        "/documents/upload",
        files={"file": ("test.pdf", file, "application/pdf")},
    )
    doc_id = upload.json()["id"]

    response = await client.post(
        f"/extractions/documents/{doc_id}/extract",
        json={"schema_name": "pay_stub"},
    )
    assert response.status_code == 400
    assert "parsed first" in response.json()["detail"].lower()
