# DataSense — Claude Code Instructions

## About this project
Building DataSense: an agentic BI copilot that takes natural language queries,
generates SQL, runs it against a database, and returns chart-ready results.
Stack: Python + FastAPI + Google Gemini API + PostgreSQL + React.
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
├── main.py          # FastAPI app entry point
├── agent.py         # Gemini tool-use agent logic
├── tools.py         # Agent tools (sql runner, schema reader)
├── db.py            # PostgreSQL connection + queries
├── evals/           # Phase 3: eval scripts
├── frontend/        # React app (Vite)
└── CLAUDE.md        # This file
```

### Python style
- Use `uv run` to execute scripts.
- Use `google-genai` SDK for all LLM calls.
- Model: `gemini-2.5-flash` (free tier, never suggest paid models).
- Store secrets in environment variables, never in code.
- Use `python-dotenv` for local `.env` files.

### Gemini API usage — minimize tokens
- Keep system prompts under 200 words.
- For SQL generation tasks, use focused single-turn calls not multi-turn.
- Cache repeated context where possible.
- Never send entire database schemas — send only relevant table schemas.

### Database
- PostgreSQL via Docker for local dev.
- Connection string from `DATABASE_URL` env variable.
- Use `psycopg2` for raw queries (simpler than an ORM for learning).

### Frontend
- React + Vite (developer already knows React).
- No UI framework — plain CSS or Tailwind only.
- Fetch from FastAPI backend at `http://localhost:8000`.

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
- [ ] Phase 3: Evals dashboard + observability + Azure deploy
- [ ] Phase 4: Design doc + portfolio polish

Update the checkbox to [x] when I tell you a phase is done.

---

## Never do these
- Never suggest paid APIs or services.
- Never add dependencies I didn't ask for.
- Never refactor working code unless I ask.
- Never generate frontend code unless I specifically ask.
- Never run `git commit` without showing me the message first.