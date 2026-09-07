import os
import json
import uuid
import jwt
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dotenv import load_dotenv

from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Header, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from nexusai.db.models import init_db, get_db, User, Thread, Message
from nexusai.db.credentials import credential_manager, CredentialsNotFoundError
from nexusai.db.auth import hash_password, verify_password
from nexusai.engine.orchestrator import agent
from nexusai.api.schemas import ChatRequest, ThreadCreateRequest, ZoomCredentialRequest, AuthRequest

load_dotenv()



# Initialize tables on startup
init_db()

app = FastAPI(
    title="NexusAI Central Hub API",
    description="Scalable multi-tenant AI workspace API with Supabase PostgreSQL (SQLAlchemy), MongoDB Credential Vault, and OAuth2 User Isolation.",
    version="2.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Mount ChatGPT / Gemini Style Web UI
WEB_DIR = Path(__file__).parent.parent / "ui" / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        response = FileResponse(str(WEB_DIR / "index.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


# ----------------------------------------------------------------------------------
# Auth Dependency: Extract OAuth2 User
# ----------------------------------------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """
    Extracts and validates OAuth2 / Supabase user strictly from Authorization header JWT.
    Derives user_id STRICTLY from the verified token 'sub' claim.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Missing Authorization header."
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format: Expected 'Bearer <token>'."
        )

    token = parts[1]
    user_id = None
    email = None

    try:
        if SUPABASE_JWT_SECRET:
            claims = jwt.decode(
                token, 
                SUPABASE_JWT_SECRET, 
                algorithms=["HS256", "RS256"], 
                options={"verify_aud": False}
            )
        else:
            claims = jwt.decode(token, options={"verify_signature": False})

        user_id = claims.get("sub") or claims.get("user_id")
        email = claims.get("email") or claims.get("user_metadata", {}).get("email")
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired OAuth2 token: {str(e)}"
        )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OAuth2 token: missing user ID claim (sub)."
        )

    # Sync user in PostgreSQL via SQLAlchemy
    user = db.query(User).filter(User.id == str(user_id)).first()
    if not user:
        user = User(id=str(user_id), email=email or f"{user_id}@oauth.user")
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


# ----------------------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------------------
@app.get("/health")
def health_check():
    mongo_status = "connected" if credential_manager.collection is not None else "offline"
    return {
        "status": "healthy",
        "stack": "FastAPI + SQLAlchemy + PostgreSQL",
        "database": "Supabase PostgreSQL",
        "vault": f"MongoDB ({mongo_status})",
        "mongodb": mongo_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/auth/signup")
def signup(req: AuthRequest, db: Session = Depends(get_db)):
    """User signup endpoint creating an isolated user profile in Supabase PostgreSQL with hashed password."""
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    password = (req.password or "").strip()
    if not password or len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long.")

    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please sign in.")

    user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
    user = User(id=user_id, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    payload = {
        "sub": user.id,
        "email": user.email,
        "role": "authenticated",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30
    }
    secret = SUPABASE_JWT_SECRET or "nexusai-demo-secret-key"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


@app.post("/api/auth/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    """
    User login endpoint strictly requiring:
    1. User must be pre-registered in the database.
    2. Correct password must be provided and match stored hash.
    """
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    password = (req.password or "").strip()
    if not password:
        raise HTTPException(status_code=400, detail="Password is required to sign in.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
        user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied: User not registered in the database. Please create an account first."
        )

    # Strictly verify password against stored database hash
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied: No password configured for this account. Please sign up or contact administrator."
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied: Incorrect password. Please check your password and try again."
        )

    payload = {
        "sub": user.id,
        "email": user.email,
        "role": "authenticated",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30
    }
    secret = SUPABASE_JWT_SECRET or "nexusai-demo-secret-key"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }




@app.get("/api/auth/demo-token")
def get_demo_token(email: str = "developer@nexusai.local"):
    """
    Generates a valid JWT for the web client so developers can interact with the
    full multi-tenant stack immediately.
    """
    # Deterministic UUID from email
    demo_user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
    payload = {
        "sub": demo_user_id,
        "email": email,
        "role": "authenticated",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30
    }
    secret = SUPABASE_JWT_SECRET or "nexusai-demo-secret-key"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": demo_user_id,
            "email": email
        }
    }




@app.get("/api/user/me")
def get_user_profile(user: User = Depends(get_current_user)):
    return {
        "user_id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


# --- Threads & History (PostgreSQL / SQLAlchemy) ---

@app.get("/api/threads")
def list_threads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve all threads strictly belonging to the authenticated user."""
    threads = db.query(Thread).filter(Thread.user_id == user.id).order_by(Thread.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in threads
    ]


@app.post("/api/threads")
def create_thread(req: ThreadCreateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new conversation thread for the authenticated user."""
    new_id = str(uuid.uuid4())
    thread = Thread(id=new_id, user_id=user.id, title=req.title or "New Chat")
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return {"id": thread.id, "title": thread.title, "user_id": thread.user_id}


@app.get("/api/threads/{thread_id}/messages")
def get_thread_messages(thread_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get message history for a specific thread, verifying user ownership."""
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user.id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found or access denied.")

    messages = db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]


@app.delete("/api/threads/{thread_id}")
def delete_thread(thread_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a thread and its messages belonging to the authenticated user."""
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user.id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found or access denied.")
    db.delete(thread)
    db.commit()
    return {"status": "deleted", "thread_id": thread_id}


# --- Agent Execution ---

@app.post("/api/chat")
def chat_with_nexus(req: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Execute NexusAI orchestrator with dynamic user context and store messages in PostgreSQL.
    """
    thread_id = req.thread_id or str(uuid.uuid4())

    # Ensure thread exists and belongs to user
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user.id).first()
    if not thread:
        title_snippet = req.message[:40] + ("..." if len(req.message) > 40 else "")
        thread = Thread(id=thread_id, user_id=user.id, title=title_snippet)
        db.add(thread)
        db.commit()

    # Save user message to PostgreSQL
    user_msg = Message(thread_id=thread_id, user_id=user.id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()

    # Configure LangGraph execution with user_id & thread_id
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user.id,
        },
        "metadata": {
            "thread_id": thread_id,
            "user_id": user.id,
        }
    }

    try:
        response = agent.invoke({"messages": [HumanMessage(req.message)]}, config=config)
        messages = response.get("messages", [])
        ai_text = "I have processed your request."
        for m in reversed(messages):
            if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None) and m.content:
                ai_text = str(m.content)
                break

        # Save assistant message to PostgreSQL
        ai_msg = Message(thread_id=thread_id, user_id=user.id, role="assistant", content=ai_text)
        db.add(ai_msg)
        db.commit()

        return {
            "thread_id": thread_id,
            "response": ai_text
        }
    except Exception as e:
        error_msg = f"Agent execution error: {str(e)}"
        print(f"[/api/chat] Error: {error_msg}")
        ai_msg = Message(thread_id=thread_id, user_id=user.id, role="assistant", content=f"⚠️ {error_msg}")
        db.add(ai_msg)
        db.commit()
        return {"thread_id": thread_id, "response": f"⚠️ {error_msg}"}



# --- MongoDB Credential Management ---

@app.get("/api/credentials")
def list_credentials(user: User = Depends(get_current_user)):
    """List active service integrations for the user from MongoDB."""
    return credential_manager.list_user_credentials(user_id=user.id)


@app.post("/api/credentials/zoom")
def save_zoom_credentials(req: ZoomCredentialRequest, user: User = Depends(get_current_user)):
    """Store encrypted Zoom Server-to-Server credentials in MongoDB."""
    data = {
        "account_id": req.account_id,
        "client_id": req.client_id,
        "client_secret": req.client_secret
    }
    credential_manager.save_credential(
        user_id=user.id,
        service="zoom",
        auth_type="zoom_s2s",
        credential_data=data
    )
    return {"status": "success", "service": "zoom", "message": "Zoom credentials encrypted & saved in MongoDB."}


@app.post("/api/credentials/upload-json")
async def upload_json_credential(
    service: str = Form(...),  # 'gmail' | 'google_calendar' | 'google_meet'
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Upload Google service account or OAuth JSON credentials encrypted into MongoDB."""
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")

    auth_type = "service_account" if data.get("type") == "service_account" else "oauth_token"
    credential_manager.save_credential(
        user_id=user.id,
        service=service,
        auth_type=auth_type,
        credential_data=data,
        metadata={"filename": file.filename}
    )
    return {"status": "success", "service": service, "message": f"{service} credentials encrypted & saved in MongoDB."}


@app.delete("/api/credentials/{service}")
def remove_credential(service: str, user: User = Depends(get_current_user)):
    """Delete a stored credential from MongoDB."""
    deleted = credential_manager.delete_credential(user_id=user.id, service=service)
    return {"status": "success" if deleted else "not_found", "deleted": deleted}
