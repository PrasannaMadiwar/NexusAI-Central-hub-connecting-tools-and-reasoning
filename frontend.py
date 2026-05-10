import uuid

import streamlit as st
from backend import agent, retrive_all_threads
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

st.set_page_config(
    page_title="NexusAI DeepAgent",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_STYLE = """
<style>
    :root {
        --bg: #0f0f0f;
        --panel: #1f1f1f;
        --sidebar: #171717;
        --sidebar-hover: #2f2f2f;
        --line: #303030;
        --text: #f8fafc;
        --muted: #c7c7c7;
        --accent: #10a37f;
        --user: #2f2f2f;
        --assistant: #1f1f1f;
    }

    html, body, .stApp {
        background: var(--bg);
        color: var(--text);
    }

    [data-testid="stAppViewContainer"] {
        background: var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: var(--bg);
    }

    [data-testid="stSidebar"] {
        background: var(--sidebar);
        border-right: 1px solid #27272a;
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        justify-content: flex-start;
        min-height: 40px;
        border: 1px solid #2f2f2f;
        border-radius: 8px;
        background: #212121;
        color: #fafafa;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--sidebar-hover);
        border-color: #3f3f46;
    }

    .main .block-container {
        max-width: 980px;
        padding-top: 1.1rem;
        padding-bottom: 7rem;
        color: var(--text);
    }

    .stMarkdown,
    .stMarkdown p,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    label,
    p,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: var(--text);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.5rem 0 0.8rem;
    }

    .brand-mark {
        display: grid;
        place-items: center;
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: var(--accent);
        color: white;
        font-weight: 800;
    }

    .brand-title {
        font-size: 1.05rem;
        font-weight: 750;
        line-height: 1.1;
    }

    .brand-subtitle {
        margin-top: 0.15rem;
        color: #a1a1aa;
        font-size: 0.78rem;
    }

    .section-label {
        margin: 1rem 0 0.45rem;
        color: #a1a1aa;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.7rem 0 1rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 1rem;
    }

    .topbar-title {
        color: var(--text);
        font-weight: 750;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.7rem;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: var(--panel);
        color: var(--text);
        font-size: 0.82rem;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--accent);
    }

    .empty-state {
        display: flex;
        min-height: 45vh;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .empty-logo {
        display: grid;
        place-items: center;
        width: 54px;
        height: 54px;
        border-radius: 14px;
        background: #202123;
        color: #ffffff;
        font-size: 1.55rem;
        font-weight: 800;
        box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
    }

    .empty-state h2 {
        margin: 1rem 0 0.25rem;
        color: var(--text);
        font-size: 2.25rem;
        letter-spacing: 0;
    }

    .empty-state p {
        max-width: 560px;
        color: var(--muted);
        margin: 0;
    }

    [data-testid="stChatMessage"] {
        max-width: 820px;
        margin: 0 auto;
        padding: 0.75rem 0;
        background: transparent;
    }

    [data-testid="stChatMessageContent"] {
        padding: 0.95rem 1.05rem;
        border: 1px solid var(--line);
        border-radius: 14px;
        background: var(--assistant);
        color: var(--text);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28);
    }

    [data-testid="stChatMessageContent"] * {
        color: var(--text);
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        background: var(--accent);
    }

    [data-testid="stChatMessageAvatarUser"] {
        background: var(--user);
    }

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background: var(--user);
        border-color: var(--user);
    }

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {
        color: #ffffff;
    }

    [data-testid="stChatInput"] {
        max-width: 900px;
        margin: 0 auto;
    }

    [data-testid="stChatInput"] textarea {
        min-height: 52px;
        border-radius: 16px;
        border: 1px solid #3a3a3a;
        background: #1f1f1f;
        color: #ffffff;
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.38);
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent);
        box-shadow: 0 18px 50px rgba(16, 163, 127, 0.18);
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #b7b7b7;
    }

    .stButton > button {
        min-height: 40px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: #1f1f1f;
        color: var(--text);
    }

    .stButton > button:hover {
        border-color: var(--accent);
        background: #2a2a2a;
        color: #ffffff;
    }

    .stButton > button * {
        color: inherit;
    }

    [data-testid="stChatInput"] {
        background: #0b0d12;
    }

    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottom"] {
        background: #0b0d12;
    }
</style>
"""

st.markdown(APP_STYLE, unsafe_allow_html=True)


# ********************************************************** utility functions *******************************************

def create_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_thread"]:
        st.session_state["chat_thread"].append(thread_id)


def new_chat():
    thread_id = create_thread_id()
    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = []
    add_thread(thread_id)


def load_conversation(thread_id):
    config_ = {"configurable": {"thread_id": thread_id}}
    messages = agent.get_state(config=config_).values
    return messages.get("messages", [])


def message_to_role(message):
    return "user" if isinstance(message, HumanMessage) else "assistant"


def messages_to_history(messages):
    return [
        {"role": message_to_role(message), "content": message.content}
        for message in messages
    ]


def title_from_text(text):
    clean_text = " ".join(str(text).split())
    if not clean_text:
        return "New chat"
    return clean_text[:38] + ("..." if len(clean_text) > 38 else "")


def chat_label(thread_id):
    if thread_id == st.session_state.get("thread_id") and st.session_state.get("message_history"):
        for message in st.session_state["message_history"]:
            if message["role"] == "user":
                return title_from_text(message["content"])

    try:
        messages = load_conversation(thread_id)
    except Exception:
        messages = []

    for message in messages:
        if isinstance(message, HumanMessage):
            return title_from_text(message.content)

    return f"New chat {str(thread_id)[:8]}"


def load_thread(thread_id):
    st.session_state["thread_id"] = thread_id
    st.session_state["message_history"] = messages_to_history(load_conversation(thread_id))


def stream_agent_response(user_input, config):
    for msg, _ in agent.stream(
        {"messages": [HumanMessage(user_input)]},
        config=config,
        stream_mode="messages",
    ):
        if isinstance(msg, AIMessage):
            yield msg.content


# ************************************************************ session set up ********************************************

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "chat_thread" not in st.session_state:
    st.session_state["chat_thread"] = retrive_all_threads()

if "queued_prompt" not in st.session_state:
    st.session_state["queued_prompt"] = None

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = create_thread_id()
    add_thread(st.session_state["thread_id"])


# ***************************************************************** sidebar ui ******************************************

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">N</div>
            <div>
                <div class="brand-title">NexusAI</div>
                <div class="brand-subtitle">DeepAgent workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("+ New chat", use_container_width=True):
        new_chat()
        st.rerun()

    st.markdown('<div class="section-label">Conversations</div>', unsafe_allow_html=True)

    for saved_thread_id in st.session_state["chat_thread"][::-1]:
        active = saved_thread_id == st.session_state["thread_id"]
        label = chat_label(saved_thread_id)
        button_label = f"> {label}" if active else label

        if st.button(button_label, key=f"thread-{saved_thread_id}", use_container_width=True):
            load_thread(saved_thread_id)
            st.rerun()


# *********************************************************** main ui **************************************************

config = {
    "configurable": {"thread_id": st.session_state["thread_id"]},
    "metadata": {"thread_id": st.session_state["thread_id"]},
    "run_name": "model_call",
}

st.markdown(
    """
    <div class="topbar">
        <div class="topbar-title">NexusAI DeepAgent</div>
        <div class="status-pill"><span class="status-dot"></span>Tools ready</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state["message_history"]:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-logo">N</div>
            <h2>How can I help?</h2>
            <p>Ask NexusAI to search, draft mail, create calendar events, analyze meetings, or run code.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Summarize a meeting", use_container_width=True):
            st.session_state["queued_prompt"] = "Summarize my latest meeting and list action items."
            st.rerun()
        if st.button("Draft an email", use_container_width=True):
            st.session_state["queued_prompt"] = "Help me draft a professional email."
            st.rerun()
    with col2:
        if st.button("Create calendar event", use_container_width=True):
            st.session_state["queued_prompt"] = "Help me create a calendar event."
            st.rerun()
        if st.button("Run or explain code", use_container_width=True):
            st.session_state["queued_prompt"] = "Help me run, debug, or explain Python code."
            st.rerun()

for msg in st.session_state["message_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

typed_input = st.chat_input("Message NexusAI...")
user_input = st.session_state["queued_prompt"] or typed_input

if user_input:
    st.session_state["queued_prompt"] = None
    st.session_state["message_history"].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        ai_message = st.write_stream(stream_agent_response(user_input, config))

    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
