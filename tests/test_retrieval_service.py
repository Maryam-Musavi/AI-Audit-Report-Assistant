from backend.services.retrieval_service import retrieve_chunk


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

    