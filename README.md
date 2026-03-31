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
- **Auth** — JWT login/register with password strength validation, real-time username availability check, brute-force lockout after 5 failed attempts.
- **Role-based access** — `admin` and `user` roles. Admin dashboard and user management gated to admins only. Roles embedded in JWT, assignable via admin UI.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           React + Vite (Vercel)             │
│   Login → Chat → Certify → Admin            │
└──────────────────────┬──────────────────────┘
                       │ /insurance/*
┌──────────────────────▼──────────────────────┐
│      FastAPI backend (Render — Docker)      │
│  auth.py  rag.py  certify.py  store.py      │
│  Rate limiting (slowapi) + security headers │
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
| Auth | JWT (python-jose) + sha256_crypt + RBAC |
| Rate limiting | slowapi |
| PDF | ReportLab |
| Frontend | React + Vite (no UI framework) |
| Containerisation | Docker + Docker Compose |
| Deployment | Render (Docker) + Vercel (UI) |

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

## Security

- JWT authentication (8-hour expiry)
- Role-based access control (`user` / `admin`) embedded in JWT
- Brute-force protection — account locked after 5 failed login attempts (15-min window)
- Rate limiting on all auth and chat endpoints (slowapi)
- Input validation — password rules, username format, message length caps
- Security headers — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- CORS restricted to known origins

---

## Project Structure

```
datasense/
├── main.py                  # FastAPI entry point
├── agent.py                 # Gemini tool-use agent (text-to-SQL)
├── Dockerfile               # Production container
├── docker-compose.yml       # Local dev (API + PostgreSQL)
├── render.yaml              # Render deploy config (Docker runtime)
├── requirements.txt         # Pinned deps fallback
├── insurance/
│   ├── auth.py              # JWT + RBAC + PostgreSQL connection pool
│   ├── store.py             # Sessions, messages, certs, activity logs, user management
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

**Option A — Docker Compose (recommended)**

```bash
git clone https://github.com/ashishballa/Datasense.git
cd Datasense

# Add your API key and JWT secret
cp .env.example .env  # fill in GOOGLE_API_KEY, JWT_SECRET

docker compose up --build
```

Backend at `http://localhost:8000`. PostgreSQL managed automatically.

**Option B — uv (faster iteration)**

```bash
# Start PostgreSQL
docker run -d --name datasense-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=datasense \
  -p 5432:5432 postgres:16

# Ingest insurance PDFs (one-time)
uv run python insurance/ingest.py

# Start backend
uv run uvicorn main:app --reload
```

**Frontend (both options)**

```bash
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`

---

## Promote a user to admin

Run in Supabase SQL editor (or any psql session):

```sql
UPDATE insurance_users SET role = 'admin' WHERE username = 'your-username';
```

Sign out and back in — the Admin button will appear.

---

## Phases

- [x] Phase 1: LLM + tool use basics
- [x] Phase 2: Text-to-SQL agent + FastAPI + React UI
- [x] Phase 3: Insurance RAG chatbot + certification flow + deployment
- [x] Phase 3+: Security hardening, RBAC, Docker, admin dashboard
- [ ] Phase 4: Design doc + portfolio polish
