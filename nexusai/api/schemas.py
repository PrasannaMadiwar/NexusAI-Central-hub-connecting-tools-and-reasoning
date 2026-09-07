from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    message: str


class ThreadCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"


class ZoomCredentialRequest(BaseModel):
    account_id: str
    client_id: str
    client_secret: str


class AuthRequest(BaseModel):
    email: str
    password: Optional[str] = None

