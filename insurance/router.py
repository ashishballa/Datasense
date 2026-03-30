import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from .auth import register_user, authenticate_user, create_access_token, get_current_user, username_exists
from .rag import chat, chat_stream, clear_session
from .certify import get_steps, autofill_from_chat, generate_certificate
from .store import create_session, get_user_sessions, log_certificate, get_stats, log_event, get_failed_attempts

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/insurance", tags=["insurance"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_length(cls, v):
        if len(v) > 30:
            raise ValueError("Username too long (max 30 chars)")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) > 128:
            raise ValueError("Password too long (max 128 chars)")
        return v

@router.get("/auth/check-username/{username}")
def check_username(username: str):
    return {"available": not username_exists(username)}

@router.post("/auth/register")
@limiter.limit("10/hour")
def register(request: Request, req: RegisterRequest):
    register_user(req.username, req.password)
    log_event("register", req.username)
    return {"message": "User registered"}

@router.post("/auth/login")
@limiter.limit("20/hour;5/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    # Check lockout
    failed = get_failed_attempts(form.username, LOCKOUT_MINUTES)
    if failed >= MAX_FAILED_ATTEMPTS:
        log_event("login_blocked", form.username, f"{failed} failed attempts")
        raise HTTPException(
            status_code=429,
            detail=f"Account temporarily locked after {MAX_FAILED_ATTEMPTS} failed attempts. Try again in {LOCKOUT_MINUTES} minutes."
        )
    if not authenticate_user(form.username, form.password):
        log_event("login_failed", form.username)
        remaining = MAX_FAILED_ATTEMPTS - failed - 1
        raise HTTPException(
            status_code=401,
            detail=f"Invalid credentials. {remaining} attempt(s) remaining before lockout."
        )
    token = create_access_token(form.username)
    log_event("login", form.username)
    return {"access_token": token, "token_type": "bearer"}

# ── Chatbot ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def message_length(cls, v):
        if len(v) > 2000:
            raise ValueError("Message too long (max 2000 chars)")
        return v.strip()

@router.post("/chat/stream")
@limiter.limit("60/minute")
def insurance_chat_stream(request: Request, req: ChatRequest, username: str = Depends(get_current_user)):
    session_id = req.session_id or str(uuid.uuid4())
    create_session(session_id, username)
    log_event("chat", username, req.message[:100])
    def event_stream():
        for token in chat_stream(req.message, session_id):
            yield f"data: {token}\n\n"
        yield f"data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"X-Session-Id": session_id})

@router.delete("/chat/{session_id}")
def end_session(session_id: str, username: str = Depends(get_current_user)):
    clear_session(session_id)
    return {"message": "Session cleared"}

@router.get("/sessions")
def list_sessions(username: str = Depends(get_current_user)):
    return {"sessions": get_user_sessions(username)}

# ── Certification flow ────────────────────────────────────────────────────────

@router.get("/certify/steps")
def certification_steps(username: str = Depends(get_current_user)):
    return {"steps": get_steps()}

class AutofillRequest(BaseModel):
    chat_history: list[dict]

    @field_validator("chat_history")
    @classmethod
    def history_limit(cls, v):
        return v[-50:]  # cap at last 50 messages

@router.post("/certify/autofill")
@limiter.limit("20/minute")
def autofill(request: Request, req: AutofillRequest, username: str = Depends(get_current_user)):
    extracted = autofill_from_chat(req.chat_history)
    return {"fields": extracted}

class CertifyRequest(BaseModel):
    form_data: dict

@router.post("/certify/generate")
@limiter.limit("10/hour")
def generate_cert(request: Request, req: CertifyRequest, username: str = Depends(get_current_user)):
    log_certificate(username, req.form_data)
    log_event("certificate_generated", username, req.form_data.get("address", ""))
    pdf_bytes = generate_certificate(req.form_data, username)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=insurance_certificate.pdf"},
    )

# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/stats")
def admin_stats(username: str = Depends(get_current_user)):
    return get_stats()
