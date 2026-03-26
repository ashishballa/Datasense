# DataSense

An agentic BI copilot that translates natural language questions into SQL, executes them against a PostgreSQL database, and returns plain English answers with chart-ready data.

## Demo

Ask: *"Which customer spent the most money?"*

Returns: *"Carol spent the most, totalling $2,029.97"* — along with the raw data and the generated SQL.

## Architecture

```
User (React UI)
    ↓ POST /query
FastAPI backend
    ↓
Gemini 2.5 Flash (tool use)
    ↓ calls run_sql()
PostgreSQL
    ↓ results
Gemini 2.5 Flash (natural language answer)
    ↓
User
```

## Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Backend | Python + FastAPI |
| Database | PostgreSQL (Docker) |
| Frontend | React + Vite |
| Observability | Query logs table (question, SQL, tokens, timestamp) |
| Evals | Result-based test suite |

## Features

- **Natural language to SQL** — Gemini generates PostgreSQL queries from plain English
- **Tool use agent** — two-turn conversation loop: generate SQL → run it → answer in English
- **Dynamic schema** — reads live table structure from `information_schema`, no hardcoding
- **Observability** — every query logged with generated SQL, answer, and token usage
- **Error handling** — off-topic questions rejected gracefully
- **Evals** — result-based test suite to validate SQL correctness

## Project Structure

```
datasense/
├── main.py          # FastAPI app — POST /query, GET /logs
├── agent.py         # Gemini tool-use agent + DB setup
├── tool_use.py      # Phase 1 tool use demo
├── evals/
│   └── run_evals.py # Result-based eval suite
├── frontend/        # React + Vite UI
│   └── src/
│       ├── App.jsx
│       └── App.css
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

# Set environment variables
cp .env.example .env
# Add your GOOGLE_API_KEY from https://aistudio.google.com/apikey

# Install backend deps and start API
uv run uvicorn main:app --reload

# Install frontend deps and start UI
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173` and start asking questions.

## Phases

- [x] Phase 1: LLM + tool use basics
- [x] Phase 2: Text-to-SQL agent + FastAPI + React UI
- [ ] Phase 3: Evals dashboard + observability + Azure deploy
- [ ] Phase 4: Design doc + portfolio polish
