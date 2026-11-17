def chunk_pages(page_records, chunk_size=1000):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    chunks = []

    for page in page_records:
        text = page["text"]

        for start in range(0, len(text), chunk_size):
            chunk_text = text[start:start + chunk_size]

            if not chunk_text.strip():
                continue

            chunk = {
                "source": page["source"],
                "page_number": page["page_number"],
                "text": chunk_text,
            }
            chunks.append(chunk)

    return chunks
