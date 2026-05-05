import io


async def test_upload_document(client):
    """Test that uploading a file creates a document record with pending status."""
    file = io.BytesIO(b"%PDF-1.4 fake content")
    response = await client.post(
        "/documents/upload",
        files={"file": ("test.pdf", file, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "pending"
    assert "id" in data


async def test_list_documents_empty(client):
    response = await client.get("/documents/")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_document_not_found(client):
    response = await client.get("/documents/999")
    assert response.status_code == 404
