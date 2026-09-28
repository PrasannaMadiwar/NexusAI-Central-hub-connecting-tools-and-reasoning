# NexusAI Central Hub

NexusAI Central Hub is a scalable, multi-tenant AI workspace and reasoning hub that routes user requests to specialized agents for web search, Gmail tasks, Google Calendar scheduling, Google Meet/Zoom transcript analysis, and sandboxed Python code execution.

Built from the ground up following **Low-Level Design (LLD)** principles and optimized to run with high responsiveness on cloud free tiers (Render, Fly.io, Railway, Supabase Free Tier) with minimal memory overhead (< 80MB RAM).

---

## Architecture & Low-Level Design (LLD)

NexusAI adheres to strict software design principles and a decoupled layered architecture:

```
nexusai/
├── api/                         # Presentation Layer (HTTP / REST Controllers)
│   ├── dependencies.py          # Dependency Inversion (DIP): Injects Repositories & Services
│   ├── schemas.py               # Pydantic Request/Response DTOs
│   ├── server.py                # Composition Root & Application Factory
│   └── routers/                 # Single Responsibility Principle (SRP)
│       ├── auth.py              # User authentication & token issuance
│       ├── chat.py              # Agent reasoning orchestration endpoints
│       ├── credentials.py       # Encrypted multi-tenant credential vault
│       ├── threads.py           # User-isolated conversation sessions
│       └── health.py            # System health diagnostics
│
├── core/                        # Domain Core
│   └── exceptions.py            # Clean domain-level exception hierarchy
│
├── repositories/                # Data Access Layer (SRP, DIP)
│   ├── base.py                  # Abstract Base Repository interface
│   ├── user_repository.py       # User persistence
│   └── thread_repository.py     # Thread and Message persistence
│
├── services/                    # Business Logic Layer (SRP, DIP)
│   ├── auth_service.py          # Password hashing (PBKDF2) & JWT verification
│   ├── chat_service.py          # Orchestrator execution & conversation persistence
│   └── credential_service.py    # Credential vault operations
│
├── db/                          # Database & Security
│   ├── models.py                # SQLAlchemy ORM models with connection pooling
│   └── credentials.py           # Multi-tenant AES-256 Fernet vault
│
├── engine/                      # AI Reasoning & Execution
│   ├── orchestrator.py          # LangGraph DeepAgent orchestrator
│   └── subagents/               # Specialized subagents (Calendar, Mail, Meet, Code)
│
└── ui/                          # Frontend Presentation
    └── web/                     # Lightweight Vanilla Web UI (HTML5, CSS3, JS)
```

### LLD Highlights & Scalability
- **Single Responsibility Principle (SRP):** Routers handle HTTP translation, Services execute business rules, and Repositories handle database persistence.
- **Dependency Inversion Principle (DIP):** Routers do not construct database connections or business logic directly; dependencies are injected via FastAPI `Depends()`.
- **Zero Streamlit Overhead (Free-Tier Optimized):** Unlike Streamlit (which consumes 300MB–600MB RAM, re-runs scripts on every click, and frequently crashes on free-tier 512MB RAM limits), NexusAI features a high-performance Vanilla HTML5/CSS3/JavaScript frontend served directly by FastAPI. Memory footprint is under 80MB.
- **Connection Pooling & Auto-Reconnection:** SQLAlchemy and `psycopg_pool` are tuned for free-tier connection limits (Supabase transaction pooler, `pool_pre_ping=True`, `max_size=3`).
- **Strict Multi-Tenancy & Zero Local Fallbacks:** User credentials and chat sessions are strictly isolated using OAuth2 JWT claims (`sub`). No local secrets or shared state are ever used.

---

## Features

- **ChatGPT / Gemini Style Web UI:** Dark mode, responsive sidebar, conversation management, credential modals, and real-time status.
- **Main DeepAgent Orchestrator:** LangGraph reasoning with automated delegation to specialist agents.
- **Web Search:** DuckDuckGo real-time web search.
- **Gmail Automation:** Read, search, summarize, create drafts, and send emails via user-authenticated tokens.
- **Google Calendar:** Event scheduling and follow-up management.
- **Meeting Intelligence:** Google Meet and Zoom transcript processing and summarization.
- **Sandboxed Code Execution:** Secure Python execution via Daytona.
- **Encrypted Credential Vault:** Per-user AES-256 credential storage in MongoDB Atlas.
- **Persistent State:** Checkpointing via Supabase PostgreSQL with local SQLite fallback.

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- OpenAI API Key (or Groq API key)
- Optional: Supabase PostgreSQL URL and MongoDB URI for persistent multi-tenancy

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/PrasannaMadiwar/NexusAI-Central-hub-connecting-tools-and-reasoning.git
cd NexusAI-Central-hub-connecting-tools-and-reasoning

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies (zero heavy frontend packages)
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory (refer to `.env.example`):

```env
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# Supabase PostgreSQL (Transaction Pooler port 6543 or Session port 5432)
SUPABASE_POSTGRES_URL=postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres

# MongoDB Vault (Atlas or local container)
MONGO_URI=mongodb+srv://[USER]:[PASSWORD]@[CLUSTER].mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=nexusai
ENCRYPTION_KEY=your_fernet_aes256_base64_key
```

### 4. Running the Application

Launch the unified FastAPI server and web interface:

```bash
python frontend.py
```

Or run directly with Uvicorn:

```bash
uvicorn nexusai.api.server:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
```text
http://127.0.0.1:8000
```

---

## Running with Docker / Docker Compose

To run the complete stack including the application and local MongoDB container:

```bash
docker compose up -d
```

Access the web interface at `http://localhost:8000`.

---

## Deployment on Free Tier (e.g. Render)

NexusAI is pre-configured for free-tier cloud deployment using `render.yaml` and `Dockerfile`:

1. Fork or push this repository to GitHub.
2. Log into [Render Dashboard](https://dashboard.render.com/) and click **New** -> **Blueprint**.
3. Select your repository. Render will automatically parse `render.yaml` and configure the service:
   - **Plan:** Free (512MB RAM)
   - **Health Check:** `/health`
   - **Port:** Dynamically bound to `$PORT`
4. Set your environment variables in the Render dashboard and deploy!

---

## Running the Automated Test Suite

Run the full test suite with pytest:

```bash
python -m pytest tests/ -v
```

All 22 production tests validate JWT authorization, password security, strict tenant isolation, AES-256 vault encryption, database persistence, and deployment configuration readiness.
