"""Small API for processing one PDF and retrieving evidence from it."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.paths import GENERATED
from backend.services.document_service import process_document, retrieve_evidence

app = FastAPI(title="AI Audit Report Assistant")
MAX_PDF_BYTES = 10 * 1024 * 1024
document_chunks = []


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=20)


@app.get("/health")
def health():
    return {"status": "ok", "document_loaded": bool(document_chunks)}


@app.post("/documents")
def upload_document(file: UploadFile = File(...)):
    filename = (file.filename or "").replace("\\", "/").split("/")[-1]
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Select a PDF file.")

    content = file.file.read(MAX_PDF_BYTES + 1)
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF must be at most 10 MB.")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The file is not a valid PDF.")

    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("Password-protected PDFs are not supported.")
        with TemporaryDirectory(dir=GENERATED) as directory:
            pdf_path = Path(directory) / "upload.pdf"
            pdf_path.write_bytes(content)
            chunks = process_document(pdf_path)
    except (pymupdf.FileDataError, pymupdf.EmptyFileError, ValueError):
        raise HTTPException(
            status_code=422, detail="PDF cannot be read or contains no extractable text."
        ) from None

    for chunk in chunks:
        chunk["source"] = filename
    document_chunks[:] = chunks
    return {"filename": filename, "chunk_count": len(chunks)}


@app.post("/search")
def search(request: SearchRequest):
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be blank.")
    if not document_chunks:
        raise HTTPException(status_code=400, detail="Upload a PDF first.")
    evidence = retrieve_evidence(request.question, document_chunks, top_k=request.top_k)
    return {"evidence": evidence}
