from backend.services.retrieval_service import retrieve_chunk
from backend.paths import PDF_PATH
from backend.services.document_service import process_document

def test_retrieve_ranks_matching_chunks():
    chunks = [
    {"source": "report.pdf", 
     "page_number": 1, 
     "text": "جمع دارایی شرکت"
     },
    {"source": "report.pdf", 
     "page_number": 2, 
     "text": "جمع بدهی شرکت"
     },
    ]
    
    results = retrieve_chunk("جمع بدهی", chunks)

    assert results[0]["page_number"] == 2
    assert results[0]["score"] == 2

def test_retrieve_returns_empty_when_no_words_match():
    chunks = [
        {"source": "report.pdf",
            "page_number": 1,
            "text": "جمع دارایی شرکت"
        },
       
    ]
    results = retrieve_chunk("بدهی", chunks)

    assert results == []
    
def test_retrieve_from_sample_pdf():
    chunks = process_document(PDF_PATH)

    results = retrieve_chunk("134,341,922", chunks)

    assert results[0]["page_number"] == 1
    assert "134,341,922" in results[0]['text']

def test_retrieve_respects_top_k():
    chunks = [
        {
            "source": "report.pdf",
            "page_number": 1,
            "text": "جمع دارایی شرکت",
        },
        {
            "source": "report.pdf",
            "page_number": 2,
            "text": "جمع بدهی شرکت",
        }
    ]
    results = retrieve_chunk("جمع بدهی", chunks, top_k=1)

    assert len(results) == 1
    assert results[0]["page_number"] == 2


def test_retireive_number_with_different_seperators():
    chunks = [
        {
            "source": "report.pdf",
            "page_number": 1,
            "text": "134,341,922 سرمایه", 
        }
    ]
    results = retrieve_chunk("134.341.922", chunks)

    assert results != []



    

    