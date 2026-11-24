import re

from backend.utils.text import norm


def _words(text):
    return set(re.findall(r"\d+(?:[,.]\d+)*|[^\W\d_]+", norm(text)))

def retrieve_chunk(question, chunks, top_k=3):
    if top_k <= 0:
        raise ValueError("top_k must be greater then zero.")
    
    question_words = _words(question)
    if not question_words:
        return []
    
    results = []

    for chunk in chunks:
        chunk_words = _words(chunk["text"])
        score = len(question_words & chunk_words)

        if score > 0:
            results.append({**chunk, "score": score})

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]
