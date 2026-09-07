"""
NexusAI SubAgents: Calendar, Mail, Meet/Zoom, and Code Execution.
"""
from nexusai.engine.subagents.calendar import calendar_workflow, callWorkFlow, create_calendar_event
from nexusai.engine.subagents.mail import (
    mail_workflow,
    gmailWorkFlow,
    search_gmail_messages,
    get_gmail_message,
    send_gmail_message,
    create_gmail_draft,
)
from nexusai.engine.subagents.meet import (
    meet_workflow,
    meetWorkFlow,
    list_google_meet_transcripts,
    get_google_meet_transcript,
    list_zoom_transcripts,
    get_zoom_transcript,
    list_meet_transcripts,
    read_transcript,
)
from nexusai.engine.subagents.code import code_agent, codeAgent, LazyCodeAgent

__all__ = [
    "calendar_workflow",
    "callWorkFlow",
    "create_calendar_event",
    "mail_workflow",
    "gmailWorkFlow",
    "search_gmail_messages",
    "get_gmail_message",
    "send_gmail_message",
    "create_gmail_draft",
    "meet_workflow",
    "meetWorkFlow",
    "list_google_meet_transcripts",
    "get_google_meet_transcript",
    "list_zoom_transcripts",
    "get_zoom_transcript",
    "list_meet_transcripts",
    "read_transcript",
    "code_agent",
    "codeAgent",
    "LazyCodeAgent",
]
