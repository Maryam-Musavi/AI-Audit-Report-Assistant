import pytest

from backend.services import document_service


def test_process_and_retrieve_preserves_source_and_page(monkeypatch, tmp_path):
    monkeypatch.setattr(
        document_service, "extract_all_pages", lambda path: ["متن دیگر", "جمع بدهی ها 123"]
    )
    chunks = document_service.process_document(tmp_path / "report.pdf")

    results = document_service.retrieve_evidence("جمع بدهی", chunks)

    assert len(results) == 1
    assert results[0]["source"] == "report.pdf"
    assert results[0]["page_number"] == 2
    assert results[0]["text"] == "جمع بدهی ها 123"
    assert document_service.retrieve_evidence("ناموجود", chunks) == []


def test_process_rejects_pdf_without_extractable_text(monkeypatch, tmp_path):
    monkeypatch.setattr(document_service, "extract_all_pages", lambda path: [" ", ""])
    with pytest.raises(ValueError, match="no extractable text"):
        document_service.process_document(tmp_path / "empty.pdf")


def test_retrieve_real_sample():
    from backend.paths import PDF_PATH

    chunks = document_service.process_document(PDF_PATH)
    results = document_service.retrieve_evidence("134,341,922", chunks)

    assert any(result["page_number"] == 1 and "134,341,922" in result["text"] for result in results)
