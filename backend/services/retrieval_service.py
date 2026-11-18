from backend.utils.text import norm

def retrieve_chunk(question, chunks, top_k=3):
    if top_k <= 0:
        raise ValueError("top_k must be greater then zero.")
    
    question_words = set(norm(question).split())
    if not question_words:
        return []
    
    results = []

    for chunk in chunks:
        chunk_words = set(norm(chunk["text"]).split())
        score = len(question_words & chunk_words)

        if score > 0:
            results.append({**chunk, "score": score})

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]