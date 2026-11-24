"""Process one PDF and retrieve passages with their source locations."""

from pathlib import Path

from backend.services.chunk_service import chunk_pages
from backend.services.pdf_service import extract_all_pages
from backend.services.retrieval_service import retrieve_chunk


def process_document(pdf_path, chunk_size=1000):
    """Extract a PDF into page-aware chunks for subsequent questions."""
    path = Path(pdf_path)
    pages = extract_all_pages(path)
    records = [
        {"source": path.name, "page_number": number, "text": text}
        for number, text in enumerate(pages, start=1)
    ]
    chunks = chunk_pages(records, chunk_size=chunk_size)
    if not chunks:
        raise ValueError("The PDF contains no extractable text; a text-based PDF is required.")
    return chunks


def retrieve_evidence(question, chunks, top_k=3):
    """Return matching passages, or an empty list when none match."""
    return retrieve_chunk(question, chunks, top_k=top_k)
