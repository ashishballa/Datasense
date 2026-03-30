# DataSense — Claude Code Instructions

## About this project
Building DataSense: a home insurance RAG chatbot + agentic BI copilot.
Stack: Python + FastAPI + Google Gemini API + PostgreSQL + ChromaDB + LangChain + React + Vite.
Deployed: Render (backend) + Vercel (frontend) + Supabase (PostgreSQL).
Developer: Python beginner, strong React + Cloud background.

---

## Token efficiency rules (follow these always)

### Responses
- Be concise. No preamble, no summaries at the end.
- No "Great question!", "Sure!", or filler phrases.
- Skip explaining what you're about to do — just do it.
- When teaching a concept, 2-3 sentences max then show code.
- Never repeat code I just wrote back to me unless fixing it.

### Code
- Write the minimal code that solves the problem.
- No placeholder comments like `# your code here` or `# TODO`.
- No docstrings unless I ask for them.
- No type hints on simple scripts (add them only on FastAPI routes).
- Prefer single files over multiple files until complexity demands splitting.

### Explanations
- When I ask "why", answer in 1-3 sentences.
- When I ask "how", show code first, explain after if needed.
- No bullet-point summaries after code blocks.
- If something is standard/obvious Python, skip the explanation.

### Errors
- When I paste an error, diagnose in 1 sentence then show the fix.
- Don't explain what the error means unless I ask.

---

## Project conventions

### File structure
```
datasense/
├── main.py               # FastAPI entry point, mounts insurance router
├── agent.py              # Gemini tool-use agent (text-to-SQL)
├── requirements.txt      # Pinned deps for Render deployment
├── render.yaml           # Render deploy config
├── insurance/
│   ├── auth.py           # JWT auth + PostgreSQL connection pool
│   ├── store.py          # DB ops: sessions, messages, certificates, stats
│   ├── rag.py            # Hybrid BM25+MMR search + streaming chat
│   ├── certify.py        # 4-step form schema + autofill + PDF generation
│   ├── router.py         # All /insurance/* endpoints
│   ├── ingest.py         # PDF ingestion into ChromaDB (run once locally)
│   └── docs/             # Home insurance PDFs
├── evals/                # SQL eval suite
├── frontend/             # React + Vite
│   └── src/insurance/    # Insurance UI components
└── CLAUDE.md
```

### Python style
- Use `uv run` to execute scripts locally.
- Use `google-genai` SDK for all LLM calls.
- Model: `gemini-2.5-flash` (free tier, never suggest paid models).
- Embeddings: `models/gemini-embedding-001`.
- Store secrets in environment variables, never in code.
- Use `python-dotenv` for local `.env` files.
- After adding a new package with `uv add`, regenerate `requirements.txt`:
  `uv export --frozen --no-dev --no-emit-project -o requirements.txt`

### Gemini API usage — minimize tokens
- Keep system prompts under 200 words.
- For SQL generation tasks, use focused single-turn calls not multi-turn.
- Never send entire database schemas — send only relevant table schemas.

### Database
- Local dev: PostgreSQL via Docker (`datasense-db` container).
- Production: Supabase (connection pooler URL).
- Connection string from `DATABASE_URL` env variable.
- Use `psycopg2` for raw queries + `SimpleConnectionPool` for pooling.

### ChromaDB
- Stored in `insurance/chroma_db/` — committed to git for deployment.
- Re-ingest only when adding new PDFs: `uv run python insurance/ingest.py`
- Free tier limit: 1000 embed requests/day — ingest uses batching + backoff.

### Frontend
- React + Vite (developer already knows React).
- No UI framework — plain CSS only.
- Local: fetches from `http://localhost:8000`.
- Production: fetches from `VITE_API_URL` env var (set in Vercel).

### Deployment
- Backend → Render (`render.yaml`), start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Frontend → Vercel, root dir: `frontend`, framework: vite
- DB → Supabase, use Transaction pooler URL (not direct IPv6)
- CORS: add Vercel URL to `ALLOWED_ORIGINS` in `main.py` and set `FRONTEND_URL` on Render
- Render free tier sleeps after 15min — UptimeRobot pings every 5min to keep it awake

---

## Learning mode
I am a Python beginner. When introducing a new Python concept:
1. Show the code.
2. Add ONE inline comment on the line that's non-obvious.
3. That's it — no further explanation unless I ask.

When I make a Python mistake, correct it and note the rule in one line.

---

## Phase tracker
- [x] Phase 1: LLM + tool use basics
- [x] Phase 2: Text-to-SQL agent + FastAPI + React UI
- [x] Phase 3: Insurance RAG chatbot + certification flow + JWT auth + deployment
- [ ] Phase 4: Design doc + portfolio polish

---

## Never do these
- Never suggest paid APIs or services.
- Never add dependencies I didn't ask for.
- Never refactor working code unless I ask.
- Never generate frontend code unless I specifically ask.
- Never run `git commit` without showing me the message first.
