import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("JWT_SECRET", "changeme-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/insurance/auth/login")

_pool: pg_pool.SimpleConnectionPool | None = None

def get_pool() -> pg_pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = pg_pool.SimpleConnectionPool(1, 10, os.environ["DATABASE_URL"])
    return _pool

from contextlib import contextmanager

@contextmanager
def get_conn():
    conn = get_pool().getconn()
    try:
        yield conn
    finally:
        get_pool().putconn(conn)

def init_users_table():
    with get_conn() as conn:
        with conn:
            conn.cursor().execute("""
                CREATE TABLE IF NOT EXISTS insurance_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

def register_user(username: str, password: str):
    try:
        with get_conn() as conn:
            with conn:
                conn.cursor().execute(
                    "INSERT INTO insurance_users (username, password_hash) VALUES (%s, %s)",
                    (username, pwd_context.hash(password))
                )
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Username already exists")

def authenticate_user(username: str, password: str) -> bool:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT password_hash FROM insurance_users WHERE username = %s", (username,))
        row = cur.fetchone()
    return row is not None and pwd_context.verify(password, row["password_hash"])

def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise ValueError
        return username
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
