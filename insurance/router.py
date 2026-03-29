import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from .auth import register_user, authenticate_user, create_access_token, get_current_user
from .rag import chat, chat_stream, clear_session
from .certify import get_steps, autofill_from_chat, generate_certificate
from .store import create_session, get_user_sessions, log_certificate, get_stats

router = APIRouter(prefix="/insurance", tags=["insurance"])

# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/register")
def register(req: RegisterRequest):
    register_user(req.username, req.password)
    return {"message": "User registered"}

@router.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form.username, form.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(form.username)
    return {"access_token": token, "token_type": "bearer"}

# ── Chatbot ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

@router.post("/chat/stream")
def insurance_chat_stream(req: ChatRequest, username: str = Depends(get_current_user)):
    session_id = req.session_id or str(uuid.uuid4())
    create_session(session_id, username)  # no-op if already exists
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

@router.post("/certify/autofill")
def autofill(req: AutofillRequest, username: str = Depends(get_current_user)):
    extracted = autofill_from_chat(req.chat_history)
    return {"fields": extracted}

class CertifyRequest(BaseModel):
    form_data: dict

@router.post("/certify/generate")
def generate_cert(req: CertifyRequest, username: str = Depends(get_current_user)):
    log_certificate(username, req.form_data)
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
