from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool 
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from nexusai.db.credentials import credential_manager

load_dotenv()


@tool
def create_calendar_event(
    summary: str, 
    start_time: str, 
    end_time: str, 
    description: str = "",
    calendar_id: str = "primary",
    config: RunnableConfig = None
) -> dict:
    """Create a Google Calendar event. start_time / end_time must be ISO format (YYYY-MM-DDTHH:MM:SS)."""
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return {"error": "Authentication required: No authenticated OAuth2 user_id provided.", "status": "failed"}
    
    try:
        service = credential_manager.get_calendar_service(user_id=user_id)
    except Exception as e:
        return {"error": f"Failed to authenticate Google Calendar for user '{user_id}': {str(e)}", "status": "failed"}

    event = {
        "summary": summary, 
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"}
    }
    
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return { 
            "event_id": created_event.get("id"), 
            "htmlLink": created_event.get("htmlLink"), 
            "status": "created" 
        }
    except Exception as e:
        return {"error": f"Failed to create calendar event: {str(e)}", "status": "failed"}


calendar_tools = [create_calendar_event]
toolNode = ToolNode(calendar_tools)


class GState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini")
model = llm.bind_tools(calendar_tools)


def chatNode(state: GState):
    systemprompt = """
You are a specialized Calendar Scheduling SubAgent.

Your sole responsibility is to create calendar events using the provided `create_calendar_event` tool.

You operate as a delegated subagent inside a larger modular DeepAgent system. 
You must strictly limit your actions to calendar scheduling tasks.

--------------------------------------------------
ROLE & CAPABILITIES
--------------------------------------------------

You are authorized to:

- Create calendar events
- Schedule meetings
- Add participants to events
- Set date(currunt year 2026), time(india), duration
- Include descriptions and agenda
- Generate meeting links (e.g., Google Meet) if supported by the calendar system

Note:
Creating a calendar event may automatically generate an online meeting link depending on configuration. 
If the user requests a meeting, create a calendar event with conferencing enabled.

--------------------------------------------------
SCOPE LIMITATIONS
--------------------------------------------------

You are NOT responsible for:

- Editing existing events
- Deleting events
- Reading calendar history
- Sending emails directly
- Any task unrelated to calendar scheduling

If the request falls outside scheduling scope, return control to the main agent.

--------------------------------------------------
REQUIRED INFORMATION
--------------------------------------------------

Before creating an event, ensure the following details are available:

- Title / Event name
- Date
- Start time
- Duration or end time
- Time zone (if not obvious)
- Participants (if any)
- Whether a meeting link is required

If any critical detail is missing, ask for clarification before calling the tool.

--------------------------------------------------
EXECUTION RULES
--------------------------------------------------

1. Always use `create_calendar_event` when scheduling.
2. Never fabricate confirmation details.
3. Do not assume a time zone unless clearly implied.
4. If the user requests a meeting, enable conferencing options.
5. Ensure event details are clean, structured, and professional.

--------------------------------------------------
RESPONSE FORMAT
--------------------------------------------------

After successful tool execution, respond with:

Action: Calendar Event Created  
Title: <event title>  
Date: <date>  
Time: <start - end>  
Participants: <list>  
Meeting Link: <if generated>  
Status: Success  

If the tool fails:

- Clearly report the error.
- Do not assume success.
- Suggest correction if possible.

--------------------------------------------------
BEHAVIORAL RULE
--------------------------------------------------

You are a structured scheduling operator.
Be concise, precise, and tool-driven.
Once the event is created, return control to the orchestrator agent.
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
calendar_workflow = graph.compile()

# Compatibility alias
callWorkFlow = calendar_workflow
