import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.main import app, document_chunks


@pytest.fixture(autouse=True)
def clear_document():
    document_chunks.clear()
    yield
    document_chunks.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def pdf_bytes():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Audit revenue 123456")
    content = document.tobytes()
    document.close()
    return content


def test_upload_and_search(client, pdf_bytes):
    assert client.get("/health").json()["document_loaded"] is False
    response = client.post("/documents", files={"file": ("report.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 200
    assert client.get("/health").json()["document_loaded"] is True
    result = client.post("/search", json={"question": "revenue"}).json()["evidence"]
    assert len(result) == 1
    assert result[0]["source"] == "report.pdf"
    assert result[0]["page_number"] == 1
    assert "123456" in result[0]["text"]
    assert client.post("/search", json={"question": "missing"}).json()["evidence"] == []


def test_validation_and_failed_upload_preserves_document(client, pdf_bytes):
    assert client.post("/search", json={"question": "revenue"}).status_code == 400
    assert client.post("/documents", files={"file": ("report.pdf", pdf_bytes)}).status_code == 200
    assert client.post("/documents", files={"file": ("fake.pdf", b"not a PDF")}).status_code == 400
    assert client.post("/documents", files={"file": ("fake.pdf", b"%PDF-invalid")}).status_code == 422
    assert client.post("/documents", files={"file": ("report.txt", pdf_bytes)}).status_code == 400
    assert client.post("/search", json={"question": "   "}).status_code == 422
    assert client.post("/search", json={"question": "revenue", "top_k": 0}).status_code == 422
    assert client.post("/search", json={"question": "revenue"}).json()["evidence"]


def test_upload_size_limit(client):
    content = b"%PDF-" + b"a" * (10 * 1024 * 1024)
    assert client.post("/documents", files={"file": ("large.pdf", content)}).status_code == 413
