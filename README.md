# NexusAI Central Hub

NexusAI Central Hub is a Streamlit-based AI workspace that routes user requests to specialized agents for web search, Gmail tasks, Google Calendar scheduling, Google Meet transcript analysis, and sandboxed Python code execution.

The main interface is a chat app in `frontend.py`. It connects to the orchestrator in `backend.py`, which uses DeepAgents, LangGraph, LangChain, Groq-hosted models, and tool-specific subagents.

## Features

- Chat-style Streamlit interface with saved conversation threads
- Main DeepAgent orchestrator with delegated subagents
- Web search through DuckDuckGo
- Gmail operations through the LangChain Gmail toolkit
- Google Calendar event creation through the Calendar API
- Google Meet transcript listing and reading through Google Drive and Docs APIs
- Sandboxed Python code execution through Daytona
- SQLite checkpointing for agent state and conversation history

## Project Structure

```text
.
|-- backend.py              # Main DeepAgent orchestrator and subagent wiring
|-- frontend.py             # Streamlit chat UI
|-- calender_agent.py       # Google Calendar scheduling subagent
|-- mailAgent.py            # Gmail operations subagent
|-- meet.py                 # Google Drive/Docs transcript helpers
|-- meetAgent.py            # Meeting transcript analysis subagent
|-- codingAgent.py          # Daytona-backed Python execution subagent
|-- requirements.txt        # Python dependencies
|-- testing.ipynb           # Notebook for experiments and manual testing
|-- .env                    # Local environment variables, not committed
`-- *.json                  # Local Google credential/token files, not committed
```

## Requirements

- Python 3.11 or newer
- A Groq API key
- Daytona credentials/configuration for code execution
- Google Cloud credentials for Gmail, Calendar, Drive, and Docs access
- Streamlit for the local UI

## Setup

1. Clone the repository:

```bash
git clone https://github.com/PrasannaMadiwar/NexusAI-Central-hub-connecting-tools-and-reasoning.git
cd NexusAI-Central-hub-connecting-tools-and-reasoning
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
DAYTONA_API_KEY=your_daytona_api_key

# Supabase PostgreSQL (for LangGraph state checkpointer & threads)
SUPABASE_POSTGRES_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# MongoDB Server (for AES-256 encrypted user credentials)
MONGO_URI=mongodb+srv://[USER]:[PASSWORD]@[CLUSTER].mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=nexusai
ENCRYPTION_KEY=your_fernet_aes256_base64_key  # Optional: generated automatically if empty
```

## Security & Multi-Tenant Isolation

NexusAI is designed with strict multi-tenancy and zero local credential fallback:
- **Supabase PostgreSQL Checkpointer:** Conversation history and checkpoints are persisted in Supabase Postgres and strictly isolated by `user_id`.
- **MongoDB Server Credential Vault:** All user credentials (Gmail OAuth tokens, Google Calendar keys, Google Meet service accounts, Zoom API keys) are stored encrypted with AES-256 (`Fernet`) in MongoDB.
- **Zero Local Fallback:** No host or local JSON files are ever used as fallbacks. Every agent tool requires an authenticated user with credentials stored in their own MongoDB document.
- **OAuth2 User Identity:** User identity is always derived from authenticated OAuth2 / Supabase JWT claims (`sub`, `email`). Users cannot impersonate other accounts.

## Running the App

Start the Streamlit UI:

```bash
streamlit run frontend.py
```

Then open the local Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

From the chat interface, you can ask NexusAI to:

- Draft, search, summarize, or send Gmail messages
- Create Google Calendar events
- List and summarize Google Meet transcripts
- Search the web
- Run, debug, or explain Python code in the Daytona sandbox

## Running Individual Modules

Most users should start with the Streamlit app. For debugging, you can also run or import individual modules:

```bash
python backend.py
python meet.py
python mailAgent.py
python meetAgent.py
```

The subagent modules are primarily designed to be imported by `backend.py`, so running them directly may only validate imports and credential setup.

## State and Local Files

The orchestrator stores conversation checkpoints in SQLite files such as:

```text
deepagent_state.db
deepagent_state.db-shm
deepagent_state.db-wal
```

These are local runtime files and should not be committed.

## Troubleshooting

- If Streamlit fails at import time, confirm all dependencies from `requirements.txt` installed successfully.
- If Groq calls fail, check `GROQ_API_KEY` in `.env`.
- If Calendar or transcript tools fail, confirm the expected Google credential JSON files exist in the project root and have access to the target resources.
- If Gmail tools request authorization, complete the OAuth flow and keep the generated `token.json` local.
- If code execution fails, verify Daytona is configured and reachable from your environment.

## Security Notes

- Do not commit `.env`, `token.json`, service account files, database files, or logs containing private data.
- Use least-privilege Google scopes where possible.
- Review generated emails, calendar events, and code execution requests before allowing agents to perform real-world actions.
