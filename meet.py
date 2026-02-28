from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = "service_account.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=credentials)


def list_meet_transcripts():
    query = (
        "mimeType='application/vnd.google-apps.document' "
        "and (name contains 'Transcript' or name contains 'transcript') "
        "and trashed=false"
    )

    response = drive_service.files().list(
        q=query,
        fields="files(id, name, createdTime, webViewLink)",
        orderBy="createdTime desc"
    ).execute()

    return response.get("files", [])


from googleapiclient.discovery import build

docs_service = build("docs", "v1", credentials=credentials)

def read_transcript(doc_id: str) -> str:
    document = docs_service.documents().get(documentId=doc_id).execute()
    content = document.get("body", {}).get("content", [])

    text = ""
    for element in content:
        if "paragraph" in element:
            for run in element["paragraph"].get("elements", []):
                text += run.get("textRun", {}).get("content", "")

    return text.strip()
