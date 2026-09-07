import os
import requests
from typing import TypedDict, Annotated, List, Dict, Any
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


# ----------------------------------------------------------------------------------
# Internal Drive & Docs Helpers for Google Meet Transcripts
# ----------------------------------------------------------------------------------
def list_meet_transcripts(user_id: str) -> List[Dict[str, Any]]:
    """
    List available Google Meet transcripts from Google Drive strictly for the given OAuth2 user.
    """
    if not user_id:
        return []

    try:
        drive_service, _ = credential_manager.get_drive_and_docs_services(user_id)
    except Exception as e:
        print(f"[meet.py] Failed to get Drive service for user '{user_id}': {e}")
        return []

    query = (
        "mimeType='application/vnd.google-apps.document' "
        "and (name contains 'Transcript' or name contains 'transcript') "
        "and trashed=false"
    )

    try:
        response = drive_service.files().list(
            q=query,
            fields="files(id, name, createdTime, webViewLink)",
            orderBy="createdTime desc"
        ).execute()

        return response.get("files", [])
    except Exception as e:
        print(f"[meet.py] Drive query error: {e}")
        return []


def read_transcript(doc_id: str, user_id: str) -> str:
    """
    Fetch the full text of a Google Meet transcript document by document ID for the given user.
    """
    if not user_id:
        return "Authentication required: No authenticated user_id provided."

    try:
        _, docs_service = credential_manager.get_drive_and_docs_services(user_id)
    except Exception as e:
        return f"Error: Google Drive/Docs not authorized for user '{user_id}': {str(e)}"

    try:
        document = docs_service.documents().get(documentId=doc_id).execute()
        content = document.get("body", {}).get("content", [])

        text = ""
        for element in content:
            if "paragraph" in element:
                for run in element["paragraph"].get("elements", []):
                    text += run.get("textRun", {}).get("content", "")

        return text.strip()
    except Exception as e:
        return f"Error reading document '{doc_id}': {str(e)}"


# ----------------------------------------------------------------------------------
# LangChain Tools for Meet & Zoom
# ----------------------------------------------------------------------------------
@tool
def list_google_meet_transcripts(config: RunnableConfig = None) -> list:
    """
    List available Google Meet transcripts from Google Drive for the current user.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return "Authentication required: No authenticated OAuth2 user_id provided."
    
    transcripts = list_meet_transcripts(user_id=user_id)
    list1 = [
        {
            "id": f.get("id"),
            "name": f.get("name"),
            "createdTime": f.get("createdTime"),
            "link": f.get("webViewLink"),
        }
        for f in transcripts
    ]

    return list1 if list1 else "No Google Meet transcripts found."


@tool
def get_google_meet_transcript(doc_id: str, config: RunnableConfig = None) -> str:
    """
    Fetch the full text of a Google Meet transcript by Google Doc ID for the current user.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return "Authentication required: No authenticated OAuth2 user_id provided."
    return read_transcript(doc_id, user_id=user_id)


@tool
def list_zoom_transcripts(config: RunnableConfig = None) -> list:
    """
    List available Zoom cloud recording transcripts for the current user.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return "Authentication required: No authenticated OAuth2 user_id provided."

    try:
        token = credential_manager.get_zoom_access_token(user_id=user_id)
    except Exception as e:
        return f"Zoom authorization error for user '{user_id}': {str(e)}"

    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get("https://api.zoom.us/v2/users/me/recordings", headers=headers, timeout=10)
        if res.status_code != 200:
            return f"Zoom API returned error ({res.status_code}): {res.text}"

        data = res.json()
        meetings = data.get("meetings", [])
        transcripts = []

        for m in meetings:
            topic = m.get("topic", "Zoom Meeting")
            meeting_id = m.get("id")
            start_time = m.get("start_time")
            for f in m.get("recording_files", []):
                file_type = f.get("file_type", "").upper()
                recording_type = f.get("recording_type", "").lower()
                if file_type == "TRANSCRIPT" or "transcript" in recording_type:
                    transcripts.append({
                        "meeting_topic": topic,
                        "meeting_id": str(meeting_id),
                        "file_id": f.get("id"),
                        "start_time": start_time,
                        "download_url": f.get("download_url"),
                    })

        return transcripts if transcripts else "No Zoom transcripts found."
    except Exception as e:
        return f"Failed to list Zoom transcripts: {str(e)}"


@tool
def get_zoom_transcript(meeting_id_or_file_id: str, config: RunnableConfig = None) -> str:
    """
    Fetch and read the text of a Zoom cloud recording transcript by meeting ID or file ID.
    """
    cfg = config or {}
    user_id = cfg.get("configurable", {}).get("user_id")
    if not user_id:
        return "Authentication required: No authenticated OAuth2 user_id provided."

    try:
        token = credential_manager.get_zoom_access_token(user_id=user_id)
    except Exception as e:
        return f"Zoom authorization error for user '{user_id}': {str(e)}"

    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Check meeting recordings
        res = requests.get(f"https://api.zoom.us/v2/meetings/{meeting_id_or_file_id}/recordings", headers=headers, timeout=10)
        download_url = None
        if res.status_code == 200:
            rec_files = res.json().get("recording_files", [])
            for f in rec_files:
                if f.get("file_type") == "TRANSCRIPT" or "transcript" in f.get("recording_type", "").lower():
                    download_url = f.get("download_url")
                    break

        if not download_url:
            # Check user recordings list to match file_id
            list_res = requests.get("https://api.zoom.us/v2/users/me/recordings", headers=headers, timeout=10)
            if list_res.status_code == 200:
                for m in list_res.json().get("meetings", []):
                    for f in m.get("recording_files", []):
                        if f.get("id") == meeting_id_or_file_id:
                            download_url = f.get("download_url")
                            break

        if not download_url:
            return f"No transcript file found matching ID '{meeting_id_or_file_id}'."

        # Download the transcript file with token auth
        file_res = requests.get(f"{download_url}?access_token={token}", timeout=15)
        if file_res.status_code == 200:
            return file_res.text[:12000]  # Return content up to safe character limit
        else:
            return f"Failed to download Zoom transcript file: {file_res.status_code} {file_res.text}"

    except Exception as e:
        return f"Error retrieving Zoom transcript: {str(e)}"


meet_tools = [
    get_google_meet_transcript,
    list_google_meet_transcripts,
    get_zoom_transcript,
    list_zoom_transcripts,
]

toolNode = ToolNode(meet_tools)


class GState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatOpenAI(model="gpt-4o-mini")
model = llm.bind_tools(meet_tools)


def chatNode(state: GState):
    systemprompt = """
You are a specialized Meeting Transcript Analysis SubAgent.

Your sole responsibility is to retrieve, analyze, summarize, and answer questions about 
Google Meet and Zoom meeting transcripts using the provided tools.

--------------------------------------------------
AVAILABLE TOOLS
--------------------------------------------------
- get_google_meet_transcript
- list_google_meet_transcripts
- get_zoom_transcript
- list_zoom_transcripts

You must use these tools to retrieve transcript data.
Never fabricate transcript content.

--------------------------------------------------
ROLE & CAPABILITIES
--------------------------------------------------
- List available meeting transcripts (Google Meet & Zoom)
- Retrieve a specific transcript
- Summarize full transcripts
- Extract structured insights
- Identify decisions and action items
- Answer user questions strictly based on transcript content
- Detect assigned tasks that may require scheduling

--------------------------------------------------
SUMMARY FORMAT
--------------------------------------------------
Meeting Summary:
- Meeting Title:
- Date:
- Participants:
- Key Discussion Points:
- Decisions Made:
- Action Items:
- Responsible Persons:
- Deadlines (if mentioned):
- Open Questions:
- Overall Outcome:

If applicable:
Calendar Scheduling Suggestions:
- Suggested Event Title:
- Proposed Date/Time:
- Participants:
- Context/Reason:
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
meet_workflow = graph.compile()

# Compatibility alias
meetWorkFlow = meet_workflow
