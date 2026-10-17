import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

load_dotenv()

# Determine database URL: Supabase PostgreSQL, or local SQLite fallback
SUPABASE_URL = os.getenv("SUPABASE_POSTGRES_URL") or os.getenv("DATABASE_URL")
if SUPABASE_URL and "sqlite" not in SUPABASE_URL:
    test_url = SUPABASE_URL.replace("postgresql://", "postgresql+psycopg://")
    try:
        # Quick 2-second connectivity check before committing to remote Postgres pool
        test_engine = create_engine(test_url, connect_args={"connect_timeout": 2}, pool_pre_ping=True)
        with test_engine.connect() as conn:
            pass
        DB_URL = test_url
        test_engine.dispose()
    except Exception as e:
        print(f"[models.py] Warning: Postgres at {SUPABASE_URL[:30]}... unreachable ({e}). Falling back to local SQLite.")
        DB_URL = "sqlite:///./nexusai.db"
else:
    DB_URL = "sqlite:///./nexusai.db"

# Create SQLAlchemy engine & session
connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {"connect_timeout": 3}
engine_kwargs = {"connect_args": connect_args, "pool_pre_ping": True}
if "sqlite" not in DB_URL:
    engine_kwargs.update({"pool_size": 5, "max_overflow": 5})
engine = create_engine(DB_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    """Authenticated OAuth2 / Supabase User"""
    __tablename__ = "nexus_users"

    id = Column(String(128), primary_key=True, index=True)  # OAuth2 'sub' / Supabase UUID
    email = Column(String(255), nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    threads = relationship("Thread", back_populates="user", cascade="all, delete-orphan")


class Thread(Base):
    """Conversation thread strictly isolated per user"""
    __tablename__ = "nexus_threads"

    id = Column(String(64), primary_key=True, index=True)  # UUID
    user_id = Column(String(128), ForeignKey("nexus_users.id"), nullable=False, index=True)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")


class Message(Base):
    """Chat message history stored in PostgreSQL"""
    __tablename__ = "nexus_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), ForeignKey("nexus_threads.id"), nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    thread = relationship("Thread", back_populates="messages")


def init_db():
    """Create tables in database if they don't exist and run light migrations."""
    Base.metadata.create_all(bind=engine)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE nexus_users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);"))
            conn.commit()
    except Exception:
        pass



def get_db():
    """FastAPI Dependency for obtaining a SQLAlchemy DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
