"""PostgreSQL persistence for chat sessions, messages, certificates, and activity logs."""
import json
import psycopg2.extras
from .auth import get_conn

def init_tables():
    with get_conn() as conn:
        with conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS insurance_sessions (
                    session_id  TEXT PRIMARY KEY,
                    username    TEXT NOT NULL,
                    created_at  TIMESTAMPTZ DEFAULT NOW(),
                    last_active TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS insurance_messages (
                    id         SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES insurance_sessions(session_id),
                    role       TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS insurance_certificates (
                    id         SERIAL PRIMARY KEY,
                    username   TEXT NOT NULL,
                    form_data  JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id         SERIAL PRIMARY KEY,
                    username   TEXT,
                    event      TEXT NOT NULL,
                    detail     TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(session_id: str, username: str):
    with get_conn() as conn:
        with conn:
            conn.cursor().execute(
                "INSERT INTO insurance_sessions (session_id, username) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (session_id, username)
            )

def touch_session(session_id: str):
    with get_conn() as conn:
        with conn:
            conn.cursor().execute(
                "UPDATE insurance_sessions SET last_active = NOW() WHERE session_id = %s",
                (session_id,)
            )

def get_user_sessions(username: str) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT session_id, created_at, last_active,
                   (SELECT COUNT(*) FROM insurance_messages m WHERE m.session_id = s.session_id) AS message_count
            FROM insurance_sessions s
            WHERE username = %s
            ORDER BY last_active DESC
            LIMIT 20
        """, (username,))
        return [dict(r) for r in cur.fetchall()]

# ── Messages ──────────────────────────────────────────────────────────────────

def save_message(session_id: str, role: str, content: str):
    with get_conn() as conn:
        with conn:
            conn.cursor().execute(
                "INSERT INTO insurance_messages (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, role, content)
            )

def load_messages(session_id: str) -> list[dict]:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT role, content FROM insurance_messages WHERE session_id = %s ORDER BY created_at",
            (session_id,)
        )
        return [dict(r) for r in cur.fetchall()]

# ── Activity logs ─────────────────────────────────────────────────────────────

def get_failed_attempts(username: str, window_minutes: int) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM activity_logs
            WHERE username = %s AND event = 'login_failed'
            AND created_at >= NOW() - INTERVAL '%s minutes'
        """, (username, window_minutes))
        return cur.fetchone()[0]

def log_event(event: str, username: str = None, detail: str = None):
    try:
        with get_conn() as conn:
            with conn:
                conn.cursor().execute(
                    "INSERT INTO activity_logs (username, event, detail) VALUES (%s, %s, %s)",
                    (username, event, detail)
                )
    except Exception:
        pass  # never let logging crash the main flow

# ── Certificates ──────────────────────────────────────────────────────────────

def log_certificate(username: str, form_data: dict):
    with get_conn() as conn:
        with conn:
            conn.cursor().execute(
                "INSERT INTO insurance_certificates (username, form_data) VALUES (%s, %s)",
                (username, json.dumps(form_data))
            )

# ── Admin stats ───────────────────────────────────────────────────────────────

def get_stats() -> dict:
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT COUNT(*) AS total FROM insurance_users")
        users = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM insurance_sessions")
        sessions = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM insurance_messages WHERE role = 'user'")
        messages = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) AS total FROM insurance_certificates")
        certs = cur.fetchone()["total"]
        cur.execute("""
            SELECT u.username,
                   COUNT(DISTINCT s.session_id) AS sessions,
                   COUNT(m.id) FILTER (WHERE m.role = 'user') AS questions,
                   u.created_at
            FROM insurance_users u
            LEFT JOIN insurance_sessions s ON s.username = u.username
            LEFT JOIN insurance_messages m ON m.session_id = s.session_id
            GROUP BY u.username, u.created_at
            ORDER BY questions DESC
            LIMIT 20
        """)
        user_rows = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT DATE(created_at) AS day, COUNT(*) AS questions
            FROM insurance_messages
            WHERE role = 'user' AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY day ORDER BY day
        """)
        daily = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT username, event, detail, created_at
            FROM activity_logs
            ORDER BY created_at DESC
            LIMIT 50
        """)
        activity = [dict(r) for r in cur.fetchall()]
    return {
        "totals": {"users": users, "sessions": sessions, "messages": messages, "certificates": certs},
        "users": user_rows,
        "daily_questions": daily,
        "activity": activity,
    }
