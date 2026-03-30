# DataSense — AI Home Insurance Assistant

A production RAG chatbot built on real home insurance policy documents. Chat with an AI assistant, auto-fill a 4-step certification form from the conversation, and download a PDF certificate.

**Live demo → [datasense-jade.vercel.app](https://datasense-jade.vercel.app)**

---

## What it does

- **Chat** — Ask anything about home insurance. Answers grounded in real policy documents, streamed token by token.
- **Autofill** — Click "Autofill from Chat" and Gemini extracts property address, coverage amounts, owner details from your conversation into the form.
- **Certification form** — 4-step dynamic form: Property → Coverage → Risk → Owner Info.
- **PDF certificate** — Generate and download a formatted certificate from completed form data.
- **Admin dashboard** — Live activity feed, stat cards, 7-day chart, user table. Auto-refreshes every 30s.
- **Auth** — JWT login/register, users persisted in PostgreSQL.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           React + Vite (Vercel)             │
│   Login → Chat → Certify → Admin            │
└──────────────────────┬──────────────────────┘
                       │ /insurance/*
┌──────────────────────▼──────────────────────┐
│           FastAPI backend (Render)          │
│  auth.py  rag.py  certify.py  store.py      │
└──────┬───────────────────────┬──────────────┘
       │                       │
┌──────▼──────┐    ┌───────────▼────────────┐
│  Supabase   │    │  ChromaDB (on disk)    │
│ PostgreSQL  │    │  890 chunks, 4 PDFs    │
└─────────────┘    └────────────────────────┘
                            │
                   Gemini 2.5 Flash ──────────
```

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Gemini Embedding 001 |
| Vector DB | ChromaDB (persistent, on disk) |
| Search | Hybrid BM25 + MMR vector search |
| Backend | Python + FastAPI |
| Database | PostgreSQL (Supabase) |
| Auth | JWT (python-jose) + sha256_crypt |
| PDF | ReportLab |
| Frontend | React + Vite |
| Deployment | Render (API) + Vercel (UI) |

---

## AI Engineering Skills Applied

- **RAG** — chunk, embed, retrieve, augment
- **Hybrid search** — BM25 keyword + MMR semantic, merged and deduplicated
- **Streaming** — SSE token streaming from LLM to browser
- **Tool use / agents** — Gemini function calling for text-to-SQL
- **LLM data extraction** — structured form autofill from unstructured chat
- **Prompt engineering** — focused system prompts, plain-text output control
- **Evals** — result-based SQL correctness test suite

---

## Project Structure

```
datasense/
├── main.py                  # FastAPI entry point
├── agent.py                 # Gemini tool-use agent (text-to-SQL)
├── requirements.txt         # Pinned deps for Render
├── render.yaml              # Render deploy config
├── insurance/
│   ├── auth.py              # JWT + PostgreSQL connection pool
│   ├── store.py             # Sessions, messages, certs, activity logs
│   ├── rag.py               # Hybrid retriever + streaming chat
│   ├── certify.py           # Form schema + autofill + PDF
│   ├── router.py            # All /insurance/* endpoints
│   ├── ingest.py            # PDF → chunks → ChromaDB
│   └── docs/                # 4 home insurance PDFs
├── evals/
│   └── run_evals.py         # SQL eval suite
└── frontend/
    └── src/
        ├── App.jsx
        └── insurance/       # Login, Chat, Certify, Admin components
```

---

## Run Locally

**Prerequisites:** Python 3.12+, Docker, Node.js

```bash
git clone https://github.com/ashishballa/Datasense.git
cd Datasense

# Start PostgreSQL
docker run -d --name datasense-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=datasense \
  -p 5432:5432 postgres:16

# Set env vars
cp .env.example .env
# Fill in GOOGLE_API_KEY, JWT_SECRET

# Ingest insurance PDFs (one-time)
uv run python insurance/ingest.py

# Start backend
uv run uvicorn main:app --reload

# Start frontend
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`

---

## Phases

- [x] Phase 1: LLM + tool use basics
- [x] Phase 2: Text-to-SQL agent + FastAPI + React UI
- [x] Phase 3: Insurance RAG chatbot + certification flow + deployment
- [ ] Phase 4: Design doc + portfolio polish
