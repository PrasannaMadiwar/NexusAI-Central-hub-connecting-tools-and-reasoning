"""
Credential Vault Router.
Manages user-scoped credentials with AES-256 encryption.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from nexusai.api.schemas import ZoomCredentialRequest
from nexusai.services.credential_service import CredentialService
from nexusai.api.dependencies import get_credential_service, get_current_user
from nexusai.db.models import User
from nexusai.core.exceptions import CredentialVaultError

router = APIRouter(prefix="/api/credentials", tags=["Credentials"])


@router.get("")
def list_credentials(
    user: User = Depends(get_current_user),
    cred_service: CredentialService = Depends(get_credential_service)
):
    """List active service integrations for the user from the vault."""
    return cred_service.list_credentials(user_id=user.id)


@router.post("/zoom")
def save_zoom_credentials(
    req: ZoomCredentialRequest,
    user: User = Depends(get_current_user),
    cred_service: CredentialService = Depends(get_credential_service)
):
    """Store encrypted Zoom Server-to-Server credentials in vault."""
    return cred_service.save_zoom_credentials(
        user_id=user.id,
        account_id=req.account_id,
        client_id=req.client_id,
        client_secret=req.client_secret
    )


@router.post("/upload-json")
async def upload_json_credential(
    service: str = Form(...),  # 'gmail' | 'google_calendar' | 'google_meet'
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    cred_service: CredentialService = Depends(get_credential_service)
):
    """Upload Google service account or OAuth JSON credentials encrypted into vault."""
    content = await file.read()
    try:
        return cred_service.save_json_credential(
            user_id=user.id,
            service=service,
            file_content=content,
            filename=file.filename
        )
    except CredentialVaultError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{service}")
def remove_credential(
    service: str,
    user: User = Depends(get_current_user),
    cred_service: CredentialService = Depends(get_credential_service)
):
    """Delete a stored credential from vault."""
    deleted = cred_service.delete_credential(user_id=user.id, service=service)
    return {"status": "success" if deleted else "not_found", "deleted": deleted}
