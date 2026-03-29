# DataSense

An agentic BI copilot + home insurance assistant. Ask data questions in plain English, get SQL-powered answers — or use the insurance assistant to chat about home coverage and generate a certificate.

## Demo

**DataSense tab** — Ask: *"Which customer spent the most money?"*
Returns: *"Carol spent the most, totalling $2,029.97"* — along with the raw data and the generated SQL.

**Insurance tab** — Ask: *"What does dwelling coverage include?"*
Returns an answer grounded in your uploaded policy documents, streamed token by token.

## Architecture

```
┌─────────────────────────────────────────────┐
│                  React + Vite               │
│   DataSense tab          Insurance tab      │
│   (SQL queries)    (RAG chat + cert form)   │
└──────────────┬──────────────────┬───────────┘
               │ POST /query      │ /insurance/*
┌──────────────▼──────────────────▼───────────┐
│              FastAPI backend                │
│  agent.py (tool use)   insurance/router.py  │
└──────────────┬──────────────────┬───────────┘
               │                  │
    ┌──────────▼───┐    ┌─────────▼──────────┐
    │  PostgreSQL  │    │  ChromaDB (on disk) │
    │  (Docker)    │    │  890 doc chunks     │
    └──────────────┘    └────────────────────┘
               │                  │
         Gemini 2.5 Flash ────────┘
```

## Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Google Gemini Embedding 001 |
| Backend | Python + FastAPI |
| Vector DB | ChromaDB (persistent, on disk) |
| Database | PostgreSQL 16 (Docker) |
| Frontend | React + Vite |
| Auth | JWT (python-jose) + sha256_crypt |

## Features

### DataSense (Text-to-SQL)
- Natural language → PostgreSQL via Gemini tool-use agent
- Dynamic schema reading from `information_schema`
- Every query logged with SQL, answer, and token usage
- Result-based eval suite

### Insurance Assistant
- **RAG chatbot** — hybrid BM25 + MMR vector search over uploaded home insurance PDFs
- **Streaming responses** — tokens streamed via SSE as they're generated
- **JWT auth** — register/login, users persisted in PostgreSQL
- **4-step certification form** — Property → Coverage → Risk → Owner Info
- **Autofill from chat** — Gemini extracts form field values from your conversation
- **PDF certificate** — generated with ReportLab and downloaded in the browser

## Project Structure

```
datasense/
├── main.py                  # FastAPI entry point
├── agent.py                 # Gemini tool-use agent (text-to-SQL)
├── insurance/
│   ├── auth.py              # JWT auth + PostgreSQL user store (connection pool)
│   ├── rag.py               # Hybrid retriever + streaming chat
│   ├── certify.py           # Certification form schema + PDF generation
│   ├── router.py            # FastAPI router (/insurance/*)
│   ├── ingest.py            # PDF ingestion into ChromaDB
│   └── docs/                # Home insurance PDFs
├── evals/
│   └── run_evals.py         # SQL eval suite
├── frontend/
│   └── src/
│       ├── App.jsx          # Tab nav (DataSense | Insurance)
│       └── insurance/       # Insurance UI components
└── pyproject.toml
```

## Getting Started

**Prerequisites:** Python 3.12+, Docker, Node.js

```bash
# Clone
git clone https://github.com/ashishballa/Datasense.git
cd Datasense

# Start PostgreSQL
docker run -d --name datasense-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=datasense \
  -p 5432:5432 postgres:16

# Environment variables
cp .env.example .env
# Add GOOGLE_API_KEY from https://aistudio.google.com/apikey
# Add JWT_SECRET (any long random string)

# Ingest insurance documents into ChromaDB
uv run python insurance/ingest.py

# Start backend
uv run uvicorn main:app --reload

# Start frontend
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`.

## Phases

- [x] Phase 1: LLM + tool use basics
- [x] Phase 2: Text-to-SQL agent + FastAPI + React UI
- [x] Phase 3: Insurance RAG chatbot + certification flow + JWT auth
- [ ] Phase 4: Azure deploy + design doc + portfolio polish
