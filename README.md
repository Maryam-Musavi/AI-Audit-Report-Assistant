# AI Audit Report Assistant — Cupcake RAG

A small learning project that uses Retrieval-Augmented Generation (RAG) to answer questions about a company's Persian audit report (PDF).

The goal is to build a simple web application while learning:
- Frontend and backend communication
- Python and FastAPI
- Cloud LLM APIs and secure API-key handling
- PDF text extraction, chunking, embeddings, and vector search
- Source-grounded answers and basic RAG evaluation

## Project Scope (MVP)

The first version intentionally supports **one PDF report at a time**.

A user should be able to:
1. Upload a PDF audit report.
2. Ask a question, such as: "Which companies has this company invested in?"
3. Receive an answer based on relevant passages retrieved from the report.
4. Review the supporting source passages and page references when available.

The system should clearly say when the report does not contain enough information. It must not invent company names, investment amounts, ownership percentages, or audit findings.

## Example Questions

- Which companies has the company invested in?
- What investment amount is reported for each investee?
- What ownership percentage is stated for each investment?
- Which investments are classified as short-term or long-term?
- What significant matters or qualified opinions did the auditor report?

These questions are examples only. Whether an answer is possible depends on the contents and quality of the selected report.

## High-Level Architecture

```text
Frontend (HTML / CSS / JavaScript)
        |
        | HTTP request / JSON or multipart form data
        v
Backend (Python / FastAPI)
        |
        +--> PDF text extraction
        |
        +--> Chunking and embeddings
        |
        +--> Vector database (Chroma)
        |
        +--> Retrieve relevant passages
        |
        +--> Cloud LLM API
        |
        v
Answer + supporting passages / page references
        |
        v
Frontend displays the result
```

**Important:** The browser must never receive the cloud provider's secret API key. Keep the key on the backend in an environment variable or a local `.env` file that is excluded from Git.

## Suggested Technology Stack

| Component | Initial choice |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Frontend-to-backend communication | Fetch API, HTTP, REST, JSON |
| Backend | Python, FastAPI |
| Cloud model | An LLM provider with an API accessible to you |
| PDF processing | A Python PDF text-extraction library |
| Embeddings | An embedding model available through a local or cloud API |
| Vector store | Chroma |
| Configuration | Environment variables and `python-dotenv` |
| Testing | FastAPI Swagger UI, browser, and a small question set |
| Version control | Git and GitHub |

Provider availability, regional restrictions, payment methods, and API terms should be checked before selecting a cloud service. Keep the LLM and embedding integrations configurable so they can be replaced later.

## Suggested Folder Structure

```text
ai-audit-report-assistant/
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── backend/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── services/
│   │   ├── pdf_service.py
│   │   ├── embedding_service.py
│   │   ├── rag_service.py
│   │   └── llm_service.py
│   ├── requirements.txt
│   └── .env.example
├── data/
│   └── .gitkeep
├── tests/
│   └── .gitkeep
├── .gitignore
└── README.md
```

This is a suggested structure, not a requirement for the first commit. Start with the smallest working version and add modules as the project grows.

## Development Roadmap

### Phase 1 — Frontend ↔ Backend

- Create a basic HTML page with a question input and an answer area.
- Create a FastAPI endpoint such as `POST /chat`.
- Send a request from JavaScript using `fetch()`.
- Return a simple JSON response from the backend.
- Learn HTTP status codes, request bodies, JSON, and error handling.

**Done when:** A question typed into the page reaches FastAPI and the response appears in the page.

### Phase 2 — Connect a Cloud LLM

- Choose an API provider that is accessible to you.
- Store the API key in a backend environment variable.
- Send the user's question from FastAPI to the model.
- Return the model's answer to the frontend.
- Handle timeouts, rate limits, invalid keys, and provider errors.
- Track token usage and estimated cost when the provider exposes this information.

**Done when:** The web page can ask a question and display a cloud model's answer without exposing the secret key.

### Phase 3 — Read an Audit PDF

- Start with a text-based PDF rather than a scanned image.
- Extract text and preserve page numbers when possible.
- Check the extracted Persian text for reading-order and encoding issues.
- Add OCR later only if scanned PDFs are required.

**Done when:** The backend can extract readable text and page references from a sample report.

### Phase 4 — Build the RAG Pipeline

- Split extracted text into chunks.
- Generate embeddings for the chunks.
- Store the vectors and useful metadata in Chroma.
- Retrieve the most relevant chunks for a question.
- Pass the retrieved context to the cloud LLM.
- Ask the model to answer only from the supplied evidence and to say when evidence is insufficient.

**Done when:** Answers are grounded in retrieved report passages rather than generated from the question alone.

### Phase 5 — Show Evidence in the Frontend

- Display the answer.
- Display supporting passages and page numbers when available.
- Clearly distinguish the model's answer from source evidence.
- Show useful error messages if a file cannot be processed or no relevant evidence is found.

**Done when:** A user can inspect the report passages supporting an answer.

### Phase 6 — Basic LLMOps and Evaluation

- Create a small test set of approximately 20–30 questions.
- Include questions whose answers are present and absent from the report.
- Compare answers with the original PDF.
- Track retrieval quality, answer quality, latency, failures, and token usage.
- Log useful metadata without unnecessarily storing sensitive report contents.

**Done when:** Changes to chunking, retrieval, prompts, or models can be compared against the same test questions.

## Example API Design

Possible endpoints for the MVP:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check whether the backend is running |
| `POST` | `/documents` | Upload and process one PDF report |
| `POST` | `/chat` | Ask a question about the processed report |

These endpoints are a starting design; they do not exist until implemented. File uploads will normally use `multipart/form-data`, while chat requests can use JSON.

## Security and Reliability

- Never commit `.env` or API keys to GitHub.
- Provide an `.env.example` containing placeholder values only.
- Validate uploaded file type and size.
- Do not trust a PDF's filename or extension alone.
- Keep cloud API calls on the backend.
- Do not send more report content to the model than needed.
- Treat retrieved document text as untrusted input, not as instructions to the model.
- Do not claim a figure or company name is present unless it can be supported by the report.
- Verify important financial facts against the cited page or table.
- Check the selected API provider's access rules, terms, and regional availability.

## Initial Acceptance Criteria

The MVP is complete when:

- [ ] A user can open the frontend in a browser.
- [ ] The frontend can communicate with the FastAPI backend.
- [ ] The user can upload one text-based PDF audit report.
- [ ] The backend extracts report text and page information where possible.
- [ ] The system retrieves relevant passages for a question.
- [ ] The backend calls a cloud LLM using a server-side API key.
- [ ] The frontend displays an answer and supporting evidence.
- [ ] The system can state that evidence is insufficient.
- [ ] Basic errors and token usage/latency are recorded where available.
- [ ] No secret keys are committed to the repository.

## Learning Principle

Build one working layer at a time:

**Frontend ↔ Backend → Cloud API → PDF processing → RAG → Evidence display → Evaluation**

Avoid adding authentication, multiple users, complex dashboards, agents, or automatic crawling of stock-market websites until the MVP works reliably.

## Disclaimer

This is an educational prototype, not an auditing, investment, or legal advice system. AI-generated answers can be incomplete or incorrect. Verify important financial information against the original report and its tables.
