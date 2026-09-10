import uuid

import streamlit as st
from nexusai.engine import agent, retrive_all_threads, save_user_credentials, get_user_integrations, remove_user_credential
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


def is_visible_assistant_message(message):
    if not isinstance(message, AIMessage):
        return False

    if getattr(message, "tool_calls", None):
        return False

    return bool(normalize_message_content(message.content).strip())


def messages_to_history(messages):
    history = []
    for message in messages:
        if isinstance(message, HumanMessage):
            history.append({"role": "user", "content": normalize_message_content(message.content)})
        elif is_visible_assistant_message(message):
            history.append({"role": "assistant", "content": normalize_message_content(message.content)})

    return history


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


def normalize_message_content(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                block_text = block.get("text") or block.get("content")
                if block_text:
                    text_parts.append(str(block_text))
        return "".join(text_parts)

    return str(content) if content else ""


def is_subagent_stream(metadata):
    if not isinstance(metadata, dict):
        return False

    graph_path = metadata.get("langgraph_path") or metadata.get("langgraph_checkpoint_ns")
    checkpoint_ns = metadata.get("checkpoint_ns")

    return bool(graph_path or checkpoint_ns)


def stream_agent_response(user_input, config):
    streamed_text = ""
    last_chunk = ""
    saw_visible_chunk = False

    for msg, metadata in agent.stream(
        {"messages": [HumanMessage(user_input)]},
        config=config,
        stream_mode="messages",
    ):
        if not isinstance(msg, AIMessage):
            continue

        if getattr(msg, "tool_calls", None):
            continue

        if is_subagent_stream(metadata):
            continue

        chunk = normalize_message_content(msg.content)
        if not chunk or chunk == last_chunk:
            continue

        last_chunk = chunk
        if chunk.startswith(streamed_text):
            delta = chunk[len(streamed_text):]
            streamed_text = chunk
        else:
            delta = chunk
            streamed_text += delta

        if delta:
            saw_visible_chunk = True
            yield delta

    if not saw_visible_chunk:
        fallback = latest_assistant_response(st.session_state["thread_id"])
        if fallback:
            yield fallback


def latest_assistant_response(thread_id):
    try:
        messages = load_conversation(thread_id)
    except Exception:
        return ""

    for message in reversed(messages):
        if is_visible_assistant_message(message):
            return normalize_message_content(message.content)

    return ""


def append_message(role, content):
    if content:
        st.session_state["message_history"].append({"role": role, "content": content})


SHORTCUT_PROMPTS = [
    (
        "Summarize all my mails",
        "Summarize all my recent unread and important emails. Group them by sender or topic, highlight urgent items, and list follow-up actions.",
    ),
    (
        "Draft a client reply",
        "Find the latest relevant client email and draft a concise professional reply with clear next steps.",
    ),
    (
        "Plan my workday",
        "Review my calendar for today, summarize meetings and deadlines, and suggest a focused work plan with priorities.",
    ),
    (
        "Schedule a follow-up",
        "Create a calendar event for a follow-up meeting based on my latest email or meeting context, including title, attendees, agenda, and timing.",
    ),
    (
        "Meeting action items",
        "Summarize my latest meeting transcript, extract decisions, owners, blockers, and action items.",
    ),
    (
        "Research for briefing",
        "Search the web for the latest updates about a company, product, or topic I mention, then prepare a short executive briefing.",
    ),
    (
        "Analyze office data",
        "Run Python on the data or code I provide, explain the results, and turn them into a professional summary I can share.",
    ),
    (
        "Weekly office digest",
        "Create a weekly work digest using my emails, calendar, meeting transcripts, web research where useful, and any code/data analysis needed.",
    ),
]


import jwt

def parse_oauth2_token(token_str: str):
    """Extract user_id and email from an OAuth2 or Supabase JWT token."""
    try:
        claims = jwt.decode(token_str, options={"verify_signature": False})
        user_id = claims.get("sub") or claims.get("user_id") or claims.get("id")
        email = claims.get("email") or claims.get("user_metadata", {}).get("email") or claims.get("preferred_username") or user_id
        return str(user_id) if user_id else None, str(email) if email else None
    except Exception:
        # If not a JWT, treat plain token/user string if formatted
        return None, None


# ************************************************************ session set up ********************************************

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# Auto-detect OAuth2 token from URL parameters (e.g., ?token=... or ?access_token=...)
query_token = st.query_params.get("token") or st.query_params.get("access_token")
if query_token and not st.session_state.get("user_id"):
    extracted_id, extracted_email = parse_oauth2_token(query_token)
    if extracted_id:
        st.session_state["user_id"] = extracted_id
        st.session_state["user_email"] = extracted_email

# Authentication Gate: Require OAuth2 / Supabase Login
if not st.session_state.get("user_id"):
    st.markdown(
        """
        <div style="max-width: 520px; margin: 3rem auto; padding: 2.2rem; border-radius: 16px; border: 1px solid #2f2f2f; background: #1a1a1a; text-align: center;">
            <div style="display: flex; justify-content: center; margin-bottom: 0.8rem;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <h2 style="margin: 0 0 0.5rem; color: #f8fafc;">NexusAI Sign In</h2>
            <p style="color: #a1a1aa; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Authenticate with your OAuth2 / Supabase identity to access your private tools, credentials, and conversation threads.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        auth_method = st.radio("Authentication Method", ["OAuth2 / Supabase JWT Token", "Supabase User Identity"], horizontal=True)

        if auth_method == "OAuth2 / Supabase JWT Token":
            raw_token = st.text_area("Paste OAuth2 / Supabase Access Token (JWT):", height=100, placeholder="eyJhbGciOi...")
            if st.button("Authenticate with Token", use_container_width=True):
                if raw_token.strip():
                    uid, uemail = parse_oauth2_token(raw_token.strip())
                    if uid:
                        st.session_state["user_id"] = uid
                        st.session_state["user_email"] = uemail
                        st.success(f"Authenticated as {uemail}!")
                        st.rerun()
                    else:
                        st.error("Invalid JWT token format or missing 'sub' / user ID claim.")
                else:
                    st.warning("Please paste your OAuth2 token.")
        else:
            login_email = st.text_input("Supabase / OAuth Email", placeholder="user@example.com")
            login_uid = st.text_input("Supabase User UUID", placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000")
            if st.button("Sign In as User", use_container_width=True):
                if login_email.strip() and login_uid.strip():
                    st.session_state["user_id"] = login_uid.strip()
                    st.session_state["user_email"] = login_email.strip()
                    st.success(f"Authenticated as {login_email}!")
                    st.rerun()
                else:
                    st.warning("Please provide both email and user UUID.")

    st.stop()


# Authenticated user state initialized
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "chat_thread" not in st.session_state:
    st.session_state["chat_thread"] = retrive_all_threads(user_id=st.session_state["user_id"])

if "queued_prompt" not in st.session_state:
    st.session_state["queued_prompt"] = None

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = create_thread_id()
    add_thread(st.session_state["thread_id"])


# ***************************************************************** sidebar ui ******************************************

with st.sidebar:
    st.markdown(
        f"""
        <div class="brand">
            <div class="brand-mark">N</div>
            <div>
                <div class="brand-title">NexusAI</div>
                <div class="brand-subtitle">DeepAgent workspace</div>
            </div>
        </div>
        <div style="padding: 0.6rem 0.8rem; margin-bottom: 0.8rem; border-radius: 8px; background: #222; border: 1px solid #333; font-size: 0.82rem;">
            <div style="color: #10a37f; font-weight: 700;">● Authenticated</div>
            <div style="color: #f8fafc; font-weight: 600; overflow: hidden; text-overflow: ellipsis;">{st.session_state.get('user_email', 'User')}</div>
            <div style="color: #71717a; font-size: 0.72rem;">ID: {str(st.session_state['user_id'])[:12]}...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_new, col_out = st.columns([2, 1])
    with col_new:
        if st.button("+ New chat", use_container_width=True):
            new_chat()
            st.rerun()
    with col_out:
        if st.button("Logout", use_container_width=True, help="Sign out of current OAuth2 session"):
            st.session_state["user_id"] = None
            st.session_state["user_email"] = None
            st.session_state["message_history"] = []
            st.session_state["chat_thread"] = []
            st.rerun()

    with st.expander("Tool Credentials & Keys", expanded=False):
        # Display active integrations strictly from MongoDB for this OAuth2 user
        try:
            active_integrations = get_user_integrations(st.session_state["user_id"])
            if active_integrations:
                st.caption(f"Active Integrations for {st.session_state.get('user_email')}:")
                for item in active_integrations:
                    col1, col2 = st.columns([3, 1])
                    col1.text(f"• {item['service']} ({item['auth_type']})")
                    if col2.button("Remove", key=f"del-{item['service']}", help="Remove credential"):
                        remove_user_credential(st.session_state["user_id"], item['service'])
                        st.rerun()
            else:
                st.caption("No credentials saved in MongoDB for your account.")
        except Exception as e:
            st.caption(f"MongoDB connection: {e}")

        st.markdown("---")
        service_to_upload = st.selectbox(
            "Connect service for this account",
            ["Gmail (token.json — OAuth2 Token)", "Google Calendar (callender_api_agent_key.json — Service Account)", "Google Meet / Drive (Service Account JSON)", "Zoom (Server-to-Server OAuth)"]
        )

        if "Zoom" in service_to_upload:
            z_account_id = st.text_input("Zoom Account ID", type="password")
            z_client_id = st.text_input("Zoom Client ID")
            z_client_secret = st.text_input("Zoom Client Secret", type="password")
            if st.button("Save Zoom Credentials"):
                if z_account_id and z_client_id and z_client_secret:
                    save_user_credentials(
                        user_id=st.session_state["user_id"],
                        service="zoom",
                        auth_type="zoom_s2s",
                        data={"account_id": z_account_id, "client_id": z_client_id, "client_secret": z_client_secret}
                    )
                    st.success("Zoom credentials encrypted & saved to MongoDB!")
                    st.rerun()
                else:
                    st.warning("Please fill all Zoom fields.")
        else:
            uploaded_file = st.file_uploader("Upload credential JSON", type=["json"])
            if uploaded_file is not None and st.button("Encrypt & Store Credential"):
                import json
                try:
                    cred_content = json.load(uploaded_file)
                    srv = "gmail" if "Gmail" in service_to_upload else ("google_calendar" if "Calendar" in service_to_upload else "google_meet")
                    auth_t = "service_account" if "type" in cred_content and cred_content.get("type") == "service_account" else "oauth_token"
                    save_user_credentials(
                        user_id=st.session_state["user_id"],
                        service=srv,
                        auth_type=auth_t,
                        data=cred_content,
                        metadata={"filename": uploaded_file.name}
                    )
                    st.success(f"{srv} credential encrypted & stored in MongoDB!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing JSON: {e}")

    st.markdown('<div class="section-label">Your Conversations</div>', unsafe_allow_html=True)

    for saved_thread_id in st.session_state["chat_thread"][::-1]:
        active = saved_thread_id == st.session_state["thread_id"]
        label = chat_label(saved_thread_id)
        button_label = f"> {label}" if active else label

        if st.button(button_label, key=f"thread-{saved_thread_id}", use_container_width=True):
            load_thread(saved_thread_id)
            st.rerun()


# *********************************************************** main ui **************************************************

config = {
    "configurable": {
        "thread_id": st.session_state["thread_id"],
        "user_id": st.session_state["user_id"],
    },
    "metadata": {
        "thread_id": st.session_state["thread_id"],
        "user_id": st.session_state["user_id"],
    },
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

    shortcut_columns = st.columns(2)
    for index, (label, prompt) in enumerate(SHORTCUT_PROMPTS):
        with shortcut_columns[index % 2]:
            if st.button(label, key=f"shortcut-{index}", use_container_width=True):
                st.session_state["queued_prompt"] = prompt
                st.rerun()

for msg in st.session_state["message_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

typed_input = st.chat_input("Message NexusAI...")
user_input = st.session_state["queued_prompt"] or typed_input

if user_input:
    st.session_state["queued_prompt"] = None
    append_message("user", user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Reasoning..."):
            ai_message = st.write_stream(stream_agent_response(user_input, config))

    ai_message = normalize_message_content(ai_message)
    if not ai_message:
        ai_message = latest_assistant_response(st.session_state["thread_id"])

    append_message("assistant", ai_message)
