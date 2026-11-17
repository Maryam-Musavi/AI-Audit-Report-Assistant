import pytest_lazyfixture

from backend.services.chunk_service import chunk_pages

def test_chunk_pages_text():
    pages = [
        {
            "source": "sample.pdf",
            "page_number": 1,
            "text": "abcdefghij",
        }
    ]

chunks = chunk_pages(pages, chunk_size=4)

assert [chunk["text"] for chunk in chunks] == [
    "abcd",
    "efgh",
    "ij",
]

def test_chunk_pages_preserves_source_and_page():
    pages = [
        {
            "source": "sample.pdf",
            "page_number": 1,
            "text": "abcd",
        },
        {
            "source": "sample.pdf",
            "page_number": 2,
            "text": "efgh",
        },
    ]

    chunks = chunk_pages(pages, chunk_size=4)

    assert len(chunks) == 2
    assert chunks[0] == pages[0]
    assert chunks[1] == pages[1]

def test_chunk_pages_skips_blank_text():
    pages = [
        {
            "source": "sample.pdf",
            "page_number": 1,
            "text": "    \n",
        }
    ]

    assert chunk_pages(pages) == []

def test_chunk_pages_handles_empty_list():
    assert chunk_pages([]) == []

def test_chunk_pages_rejects_invalid_size():
    for size in (0, -1):
        with pytest.raises(ValueError):
            chunk_pages([], chunk_size=size)