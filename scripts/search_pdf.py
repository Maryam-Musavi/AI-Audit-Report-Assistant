"""Search a text-based PDF and print matching source passages."""

import argparse

from backend.services.document_service import process_document, retrieve_evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="Path to a text-based PDF")
    parser.add_argument("question", help="Question or search terms")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    chunks = process_document(args.pdf)
    evidence = retrieve_evidence(args.question, chunks, top_k=args.top_k)
    if not evidence:
        print("No matching passages found; there is not enough evidence to answer.")
        return
    for passage in evidence:
        print(f"\n{passage['source']} | page {passage['page_number']} | score {passage['score']}")
        print(passage["text"])


if __name__ == "__main__":
    main()
