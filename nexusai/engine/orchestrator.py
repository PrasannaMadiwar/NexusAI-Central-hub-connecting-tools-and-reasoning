import os
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from deepagents import create_deep_agent, CompiledSubAgent
from langchain_openai import ChatOpenAI
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import SummarizationMiddleware
from psycopg_pool import ConnectionPool

from nexusai.db.credentials import credential_manager
from nexusai.engine.subagents.meet import meetWorkFlow
from nexusai.engine.subagents.calendar import callWorkFlow
from nexusai.engine.subagents.mail import gmailWorkFlow
from nexusai.engine.subagents.code import codeAgent

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")
internet_search = DuckDuckGoSearchRun()

meet_subagent = CompiledSubAgent(
    name="meet-analyzer",
    description=(
        "Use for every Google Meet, Zoom, transcript, meeting summary, meeting "
        "action item, or meeting question. It can list transcripts, retrieve a "
        "specific transcript, summarize it, and answer questions from transcript data."
    ),
    runnable=meetWorkFlow
)

calender_subagent = CompiledSubAgent(
   name="calendar-event-handler",
   description=(
       "Use for every Google Calendar or scheduling request, including creating "
       "calendar events, scheduling meetings, adding work tasks with a date/time, "
       "or turning follow-up details into an event."
   ),
   runnable=callWorkFlow
)

mails_subagent = CompiledSubAgent(
    name="gmail-handler",
    description=(
        "Use for every Gmail, email, inbox, mail, latest mail, unread mail, "
        "important mail, draft, send, reply, search, summarize, or explain-email "
        "request. For example: 'explain my latest mail' must be delegated here."
    ),
    runnable=gmailWorkFlow
)

code_subagent = CompiledSubAgent(
    name="code_executor",
    description=(
        "Use for every Python, code execution, data analysis, debugging, script, "
        "calculation, or sandbox execution request."
    ),
    runnable=codeAgent,
)

subagents = [code_subagent, mails_subagent, calender_subagent, meet_subagent]

store = InMemoryStore()

# Supabase PostgreSQL Checkpointer
supabase_db_url = os.getenv("SUPABASE_POSTGRES_URL") or os.getenv("DATABASE_URL")
if supabase_db_url:
    try:
        # Connect to Supabase Postgres pool
        pool = ConnectionPool(conninfo=supabase_db_url, max_size=5, kwargs={"autocommit": True})
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        print("[orchestrator.py] Connected to Supabase PostgreSQL checkpointer successfully.")
    except Exception as e:
        print(f"[orchestrator.py] Warning: Supabase Postgres connection failed ({e}). Falling back to in-memory checkpointer.")
        checkpointer = MemorySaver()
else:
    print("[orchestrator.py] Notice: SUPABASE_POSTGRES_URL not provided. Using in-memory checkpointer until configured.")
    checkpointer = MemorySaver()

composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt),
    routes={
        "/memories/": StoreBackend(rt),
    }
)

sys_prompt = """
You are NexusAI, the main orchestrator agent.

Your job is to understand the user's request, choose the correct specialist, and
return the specialist result clearly. You have access to specialist subagents
through the DeepAgents task tool.

Delegation rules:
- For any Gmail/email/mail/inbox request, call the task tool with subagent_type="gmail-handler"
  and description=<full user request plus needed context>.
  This includes: latest mail, unread mail, important mail, explain my mail, summarize mail,
  draft mail, send mail, reply to mail, and searching mail.
- For any calendar/scheduling/event request, call the task tool with subagent_type="calendar-event-handler"
  and description=<full user request plus needed context>.
- For any Google Meet, Zoom, transcript, meeting summary, or meeting action item request,
  call the task tool with subagent_type="meet-analyzer" and description=<full user request plus needed context>.
- For any Python/code/data-analysis/sandbox execution request, call the task tool with subagent_type="code_executor"
  and description=<full user request plus needed context>.
- For current web research, use the internet search tool directly unless another specialist is clearly required.

Do not answer tool-related requests from memory. If the request requires Gmail,
Calendar, Meet/Zoom transcripts, or code execution, delegate first and base your final
answer only on the returned result. If a specialist needs clarification, pass that
question back to the user.

After a subagent returns, summarize the outcome in a helpful, concise way. Mention
tool failures honestly and do not invent emails, events, transcripts, or execution
results.
"""

agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=sys_prompt,
    subagents=subagents,
    store=store,
    checkpointer=checkpointer,
    middleware=[
        SummarizationMiddleware(
            model=model,
            trigger=("tokens", 4000),
            keep=("messages", 20),
        ),
    ],
)


def retrive_all_threads(user_id: str):
    """Retrieve chat thread IDs strictly belonging to the authenticated OAuth2 user_id."""
    if not user_id:
        return []
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        cfg = checkpoint.config.get('configurable', {})
        thread_id = cfg.get('thread_id')
        if not thread_id:
            continue
        c_user = (checkpoint.metadata or {}).get('user_id') or cfg.get('user_id')
        if c_user == user_id:
            all_threads.add(thread_id)
    return list(all_threads)


def save_user_credentials(user_id: str, service: str, auth_type: str, data: dict, metadata: dict = None) -> bool:
    """Store encrypted credentials for a user in MongoDB."""
    return credential_manager.save_credential(user_id, service, auth_type, data, metadata)


def get_user_integrations(user_id: str):
    """List active integrations for a user."""
    return credential_manager.list_user_credentials(user_id)


def remove_user_credential(user_id: str, service: str) -> bool:
    """Remove stored credentials for a user."""
    return credential_manager.delete_credential(user_id, service)
