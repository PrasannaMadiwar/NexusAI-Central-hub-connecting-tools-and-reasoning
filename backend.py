from meetAgent import meetWorkFlow
from calender_agent import callWorkFlow
from mailAgent import gmailWorkFlow
from codingAgent import codeAgent
from dotenv import load_dotenv 
from langchain_community.tools import DuckDuckGoSearchRun
load_dotenv()

from deepagents import create_deep_agent, CompiledSubAgent
from langchain_groq import ChatGroq
model = ChatGroq(model="openai/gpt-oss-20b")
internet_search = DuckDuckGoSearchRun()

meet_subagent = CompiledSubAgent(
    name="meet-analyzer",
    description="Specialized agent for meet transcript summary and query response",
    runnable=meetWorkFlow
)

calender_subagent = CompiledSubAgent(
   name="calander-event-handler",
   description="specilized agent for adding events and task on the google calender",
   runnable= callWorkFlow
)

mails_subagent = CompiledSubAgent(
    name="gmail_handler",
    description="agent specilized for drafting, sending, summurizing received mails",
    runnable=gmailWorkFlow
)

code_subagent = CompiledSubAgent(
    name="code_executor",
    description="Executes Python programs securely in sandbox.",
    runnable=codeAgent,
)

subagents = [code_subagent,mails_subagent,calender_subagent,meet_subagent]
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.sqlite import SqliteSaver
from deepagents.middleware.memory import MemoryMiddleware
from langchain.agents.middleware import SummarizationMiddleware
import sqlite3

 
conn = sqlite3.connect("deepagent_state.db", check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
store = InMemoryStore()

composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt),
    routes={
        "/memories/": StoreBackend(rt),
    }
)
 
agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt="you are main-agent having multiple subagents with calender, gmail, python code exucator and google meet trancscropts retriver deleget control to them as needed",
    subagents=subagents,
    backend=composite_backend,
    store=store,
    checkpointer=checkpointer,
    middleware=[ SummarizationMiddleware(
            model=model,
            trigger=("tokens", 4000),
            keep=("messages", 20),
        ),
    ],
   
)

def retrive_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)