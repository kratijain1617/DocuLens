# DocuLens

Ask questions. See the evidence.

DocuLens is a document intelligence app for people who need an answer and the page it came from. Upload a PDF, ask in ordinary language, and read an answer that stays attached to the document name, page number, section, and original wording.

## Problem

Search inside a long PDF still drops people into a page with no explanation. A general chatbot will answer fluently even when the file never said that. Neither one is safe for a lease, a handbook, a policy, or a manual, where a wrong date or fee matters.

DocuLens answers only from retrieved passages. If those passages do not support an answer, it says so. If they disagree, it shows both.

## Who it is for

- Students reading university policies
- Renters checking a lease
- Employees reading a handbook
- Analysts comparing reports
- Anyone who has to defend an answer with a page number

The sample library covers university documents, research papers, rental agreements, handbooks, and technical manuals. The same pipeline accepts insurance documents, government forms, business reports, and financial documents.

## Features

- Landing page, sign up, login, logout, and a demo that does not need an account or an API key
- Drag-and-drop upload of one or more PDFs, with a 20 MB and 200 page limit and five documents per session
- Automatic document classification that only suggests questions
- Library with rename, delete, status, and multi-select compare
- Question answering with citations, confidence, conditions, related sections, and follow-up questions
- Click a citation to open that page and highlight the passage
- Not-found, partial, and conflicting-information states
- Side-by-side multi-document comparison
- PDF viewing with page navigation, zoom, in-document search, full screen, and download
- Cited document summaries
- Evaluation dashboard with 26 labeled questions

## Technology

| Layer | Choice |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS, React PDF |
| Charts | Recharts |
| API | FastAPI |
| PDF text | PyMuPDF |
| Chunking | LangChain text splitters |
| Vectors | Hashed TF-IDF stored per chunk, with optional OpenAI or sentence-transformer embeddings |
| Search | NumPy cosine similarity plus a lexical rerank |
| Metadata | SQLite |
| Model | Any OpenAI-compatible chat API, optional |

API keys stay on the backend. With no key, Lens answers by quoting retrieved sentences. That path is what the demo and the evaluation use.

## Architecture

```text
Browser (Next.js)
  |  REST, bearer token
FastAPI
  |-- SQLite: users, documents, chunks, questions, answers, citations
  |-- PDF files on local disk, private to the signed-in user
  |-- Index: page text -> sections -> overlapping chunks -> embeddings
  |-- Ask: embed question -> retrieve chunks -> optional LLM -> citation check
```

The browser never receives an API key. Uploaded PDFs are served only with the owner's token.

## RAG pipeline

1. PyMuPDF reads each page and keeps the page number.
2. Larger heading text becomes the section name. Header, footer, and page numbers are dropped.
3. LangChain's recursive character splitter breaks long sections into overlapping chunks of about 800 characters with 120 characters of overlap. Short sections stay intact so a citation points at one place.
4. Each chunk stores its id, document, page, section, original text, embedding, and character offsets.
5. Embeddings are a 384-dimension hashed TF-IDF vector fit on that user's chunks. Set `EMBEDDING_PROVIDER=openai` or `sentence-transformers` to use those instead.
6. The question is embedded with the same model. Retrieval mixes cosine similarity with term overlap and a boost when the section heading matches.
7. Only the top chunks go to the answer step. The full PDF is not sent.
8. Without an API key, the answer is assembled from those sentences. With a key, an OpenAI-compatible model may phrase the answer, and every quote is checked against the retrieved text.
9. Quotes that are not in a retrieved chunk are dropped. A supported answer with no surviving citation becomes "not found."

The system instruction used for the model is:

> Answer only from the supplied document context. If the context does not contain the answer, say that the information was not found. Never invent dates, fees, requirements, policies, exceptions, or conclusions.

## Citations

A citation looks like this:

```json
{
  "document_name": "Apartment Rental Agreement.pdf",
  "page_number": 3,
  "section": "Security Deposit",
  "quoted_text": "The security deposit shall be equal to one month's rent.",
  "relevance_score": 0.94
}
```

The quoted text is the original sentence. The page has to be one of the retrieved chunks. The interface shows the document, page, and section as a button. Choosing it opens the PDF on that page and highlights the passage in the text layer.

Answers use four statuses:

- `supported` — the retrieved sentences cover the question
- `partially_supported` — only part of the question is in the text
- `conflicting_information` — retrieved passages give different dates for the same question
- `not_found` — there is not enough evidence

Not-found answers use this sentence: "I could not find enough evidence in the uploaded documents to answer this confidently."

## Local setup

Use two terminals from the project root.

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:3000. The API is http://localhost:8000.

On macOS or Linux, use `source .venv/bin/activate` and `cp` instead of `copy`.

Check the pipeline without the browser:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

## Environment variables

Backend (`backend/.env`):

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Optional. Leave empty for the offline demo. |
| `OPENAI_BASE_URL` | OpenAI-compatible base URL. Default `https://api.openai.com/v1`. |
| `OPENAI_MODEL` | Chat model. Default `gpt-4o-mini`. |
| `EMBEDDING_PROVIDER` | `local` (default), `openai`, or `sentence-transformers`. |
| `EMBEDDING_MODEL` | Used when the provider is `openai`. |
| `CORS_ORIGINS` | Extra allowed origins, comma-separated. Localhost is already allowed. |
| `DATABASE_URL` | Defaults to SQLite at `backend/data/doculens.db`. |

Frontend:

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | API origin. Default `http://localhost:8000`. |

`sentence-transformers` is optional and is not installed by default. Point `EMBEDDING_PROVIDER` at it only after installing that package.

## Demo

Choose **Try Demo** on the landing page. DocuLens signs you into a demo library, builds five sample PDFs, and walks through:

1. The document library
2. "What is the security deposit?" on the Apartment Rental Agreement, with the citation opened to the highlighted page
3. A question the agreement does not answer
4. "What were the main findings?" on the research paper
5. A side-by-side attendance comparison of the university policy and the employee handbook
6. The evaluation dashboard

Pause, or open the full app, at any step. No API key is required.

Sample documents:

- University Student Policy Manual
- Apartment Rental Agreement
- Technical Product Manual
- Research Paper
- Employee Handbook

The university manual states two different course withdrawal deadlines on purpose, so the conflict state is visible.

## Evaluation

`POST /api/evaluation/run` sends 26 labeled questions through the same ask path used by the product. Each item has an expected answer, document, page, and evidence sentence. The runner records:

- Answer correctness, by overlap with the expected wording, both dates for the conflict item, or the not-found status
- Citation correctness, meaning the expected document, page, and evidence sentence were cited
- Correct page rate
- Citation grounding, meaning every quote appears in the extracted PDF text
- Retrieval hit rate, meaning the expected page was in the retrieved chunks
- Unsupported answer rate, meaning a supported or partial answer was not grounded or contradicted a not-found case
- Average response time

The Evaluation page charts those rates and lists correct and incorrect examples. On the offline demo path the smoke test currently scores every labeled question as grounded, with the expected page cited.

## Deployment

Frontend: import the repository in Vercel and set the root directory to `frontend`. Set `NEXT_PUBLIC_API_URL` to the public API URL.

Backend: Render can use the included `render.yaml`. The root directory is `backend`, and the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `CORS_ORIGINS` to the Vercel origin. Railway uses the same start command.

SQLite on a default Render disk is ephemeral. For a durable deployment, use a persistent disk or set `DATABASE_URL` to Postgres and migrate the SQLAlchemy models. Uploaded files also need persistent disk or object storage.

## Privacy and limits

DocuLens provides information based on uploaded documents. It is not legal, financial, medical, employment, or professional advice. Verify important decisions with the official source or a qualified professional.

- API keys stay on the server.
- Uploads must be PDFs within the size and page limits. The file is stored and read. It is not executed.
- Extracted text is stripped of null bytes and control characters.
- Document download requires the owner's session token.
- Users can delete documents, which removes the file, chunks, and citations.
- The app does not invent a citation for a page that was not retrieved.
- Do not upload unnecessary sensitive information. This demo stores files on the API machine.

Passwords are hashed with PBKDF2. Session tokens are stored only as SHA-256 hashes. This is a demonstration authentication design, not a complete production identity system.

## Further work

- OCR for scanned pages
- Postgres and object storage
- A hosted sentence-transformer index for larger libraries
- Stronger reranking
- Shared workspaces and SSO
- Export of an answer with its citation packet
