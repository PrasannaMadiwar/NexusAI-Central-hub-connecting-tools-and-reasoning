import base64
from email.mime.text import MIMEText
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.tools import tool 
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from nexusai.db.credentials import credential_manager

load_dotenv()


@tool
def search_gmail_messages(query: str, max_results: int = 5, config: RunnableConfig = None) -> list:
    """
    Search Gmail messages using Gmail search queries (e.g. 'is:unread', 'from:john', 'subject:report').
    Returns a list of messages with ID, snippet, sender, subject, and date.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return "Authentication required: No authenticated OAuth2 user_id provided."

    try:
        service = credential_manager.get_gmail_service(user_id=user_id)
    except Exception as e:
        return f"Gmail authentication error for user '{user_id}': {str(e)}"

    try:
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No emails found matching your query."

        output = []
        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg["id"], format="metadata").execute()
            headers = {h["name"].lower(): h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            output.append({
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "snippet": msg_data.get("snippet"),
                "from": headers.get("from", "Unknown"),
                "to": headers.get("to", "Unknown"),
                "subject": headers.get("subject", "No Subject"),
                "date": headers.get("date", "Unknown"),
            })
        return output
    except Exception as e:
        return f"Failed to search Gmail: {str(e)}"


@tool
def get_gmail_message(message_id: str, config: RunnableConfig = None) -> dict:
    """
    Retrieve the full details and body of a specific email by its message ID.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return {"error": "Authentication required: No authenticated OAuth2 user_id provided."}

    try:
        service = credential_manager.get_gmail_service(user_id=user_id)
    except Exception as e:
        return {"error": f"Gmail authentication error for user '{user_id}': {str(e)}"}

    try:
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

        def extract_body(payload):
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                        return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                for part in payload["parts"]:
                    body = extract_body(part)
                    if body:
                        return body
            elif "body" in payload and "data" in payload["body"]:
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            return msg.get("snippet", "")

        body_text = extract_body(msg.get("payload", {}))

        return {
            "id": msg["id"],
            "threadId": msg.get("threadId"),
            "from": headers.get("from"),
            "to": headers.get("to"),
            "subject": headers.get("subject"),
            "date": headers.get("date"),
            "body": body_text[:4000],  # Keep prompt token usage bounded
        }
    except Exception as e:
        return {"error": f"Failed to retrieve email '{message_id}': {str(e)}"}


@tool
def send_gmail_message(to: str, subject: str, body: str, config: RunnableConfig = None) -> dict:
    """
    Send an email via Gmail.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return {"error": "Authentication required: No authenticated OAuth2 user_id provided."}

    try:
        service = credential_manager.get_gmail_service(user_id=user_id)
    except Exception as e:
        return {"error": f"Gmail authentication error for user '{user_id}': {str(e)}"}

    try:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {
            "status": "success",
            "message_id": sent.get("id"),
            "thread_id": sent.get("threadId"),
            "to": to,
            "subject": subject
        }
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


@tool
def create_gmail_draft(to: str, subject: str, body: str, config: RunnableConfig = None) -> dict:
    """
    Create a draft email in Gmail without sending it.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return {"error": "Authentication required: No authenticated OAuth2 user_id provided."}

    try:
        service = credential_manager.get_gmail_service(user_id=user_id)
    except Exception as e:
        return {"error": f"Gmail authentication error for user '{user_id}': {str(e)}"}

    try:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return {
            "status": "success",
            "draft_id": draft.get("id"),
            "to": to,
            "subject": subject
        }
    except Exception as e:
        return {"error": f"Failed to create draft: {str(e)}"}


mail_tools = [search_gmail_messages, get_gmail_message, send_gmail_message, create_gmail_draft]
toolNode = ToolNode(mail_tools)


class GState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini")
model = llm.bind_tools(mail_tools)


def chatNode(state: GState):
    systemprompt = """
You are a specialized Gmail Operations SubAgent.

Your sole responsibility is to handle Gmail-related tasks using the provided Gmail tools:
- search_gmail_messages
- get_gmail_message
- send_gmail_message
- create_gmail_draft

--------------------------------------------------
ROLE & SCOPE
--------------------------------------------------
- Read, search, summarize, draft, and send emails.
- Always use the tools to interact with the user's inbox.
- Never fabricate email content or message IDs.

--------------------------------------------------
SAFETY & VERIFICATION
--------------------------------------------------
Before sending an email:
- Confirm recipient address is valid.
- If user intent is ambiguous, prefer creating a draft or ask for confirmation.
- Report tool output accurately.
"""
    response = model.invoke(
        [SystemMessage(content=systemprompt)] + state["messages"]
    )
    return {'messages': [response]}


graph = StateGraph(GState)
graph.add_node('chat', chatNode)
graph.add_node('tools', toolNode)
graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", tools_condition, {'tools': "tools", "__end__": END})
graph.add_edge("tools", "chat")
mail_workflow = graph.compile()

# Compatibility alias
gmailWorkFlow = mail_workflow
