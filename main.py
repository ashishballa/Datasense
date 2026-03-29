from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2.extras
from agent import ask, setup_db
from insurance.router import router as insurance_router
from insurance.auth import init_users_table

db = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    db["conn"] = setup_db()
    init_users_table()  # create insurance_users table if not exists
    yield
    db["conn"].close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
