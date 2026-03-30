import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import psycopg2.extras
from agent import ask, setup_db
from insurance.router import router as insurance_router
from insurance.auth import init_users_table
from insurance.store import init_tables as init_store_tables

db = {}
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db["conn"] = setup_db()
    init_users_table()
    init_store_tables()
    yield
    db["conn"].close()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://datasense-jade.vercel.app",
    os.getenv("FRONTEND_URL", ""),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in ALLOWED_ORIGINS if o],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

app.include_router(insurance_router)

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(req: QueryRequest):
    result = ask(req.question, db["conn"])
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/logs")
def logs():
    cur = db["conn"].cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM query_logs ORDER BY created_at DESC LIMIT 100")
    return [dict(r) for r in cur.fetchall()]
