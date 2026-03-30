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
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS insurance_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            # idempotent migration — adds role column if it doesn't exist yet
            cur.execute("""
                ALTER TABLE insurance_users
                ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
            """)

def validate_password(password: str):
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("one uppercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("one number")
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("one special character")
    if errors:
        raise HTTPException(status_code=400, detail="Password must contain: " + ", ".join(errors))

def username_exists(username: str) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM insurance_users WHERE username = %s", (username,))
        return cur.fetchone() is not None

def register_user(username: str, password: str):
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if not username.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, - and _")
    validate_password(password)
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

def get_user_role(username: str) -> str:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT role FROM insurance_users WHERE username = %s", (username,))
        row = cur.fetchone()
    return row[0] if row else "user"

def set_user_role(username: str, role: str):
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    with get_conn() as conn:
        with conn:
            cur = conn.cursor()
            cur.execute("UPDATE insurance_users SET role = %s WHERE username = %s", (role, username))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

def create_access_token(username: str, role: str = "user") -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "role": role, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def _decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise ValueError
        return payload
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    return _decode_token(token)["sub"]

def require_admin(token: str = Depends(oauth2_scheme)) -> str:
    payload = _decode_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload["sub"]
