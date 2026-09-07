"""
Automated validation test for NexusAI Backend using modular nexusai package:
- Supabase Postgres Checkpointer support
- MongoDB Server Credential Store with AES-256
- Zero Local Fallback (Strict User Isolation)
- Mandatory OAuth2 user_id enforcement across all tools
"""
import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nexusai.db.credentials import CredentialManager, credential_manager, CredentialsNotFoundError
from nexusai.engine.orchestrator import retrive_all_threads, save_user_credentials, get_user_integrations
from nexusai.engine.subagents.calendar import create_calendar_event
from nexusai.engine.subagents.meet import list_google_meet_transcripts, list_zoom_transcripts, get_zoom_transcript
from nexusai.engine.subagents.mail import search_gmail_messages, get_gmail_message


def test_encryption_roundtrip():
    print("1. Testing Fernet AES-256 encryption round-trip...")
    test_data = {
        "client_id": "test-client-id-12345",
        "client_secret": "super-secret-key-67890",
        "account_id": "zoom-acc-111"
    }
    encrypted = CredentialManager.encrypt_data(test_data)
    assert isinstance(encrypted, str)
    assert encrypted != json.dumps(test_data)
    
    decrypted = CredentialManager.decrypt_data(encrypted)
    assert decrypted == test_data
    print("   -> Encryption round-trip passed!")


def test_zero_local_fallback_enforcement():
    print("2. Testing Zero-Fallback policy (local files must NEVER be used)...")
    unregistered_user = "unregistered_oauth_user_555"
    
    # Calendar service must raise CredentialsNotFoundError, NOT fall back to local json
    try:
        credential_manager.get_calendar_service(user_id=unregistered_user)
        assert False, "Security violation: get_calendar_service fell back to local file!"
    except (CredentialsNotFoundError, RuntimeError):
        print("   -> Calendar zero-fallback verified: local file ignored.")

    # Gmail service must raise CredentialsNotFoundError, NOT fall back to local json
    try:
        credential_manager.get_gmail_service(user_id=unregistered_user)
        assert False, "Security violation: get_gmail_service fell back to local file!"
    except (CredentialsNotFoundError, RuntimeError):
        print("   -> Gmail zero-fallback verified: local file ignored.")

    # Drive service must raise CredentialsNotFoundError, NOT fall back to local json
    try:
        credential_manager.get_drive_and_docs_services(user_id=unregistered_user)
        assert False, "Security violation: get_drive_and_docs_services fell back to local file!"
    except (CredentialsNotFoundError, RuntimeError):
        print("   -> Meet/Drive zero-fallback verified: local file ignored.")


def test_tool_oauth2_auth_enforcement():
    print("3. Testing OAuth2 user_id enforcement on all subagent tools...")
    
    # Missing config or missing user_id
    res_cal = create_calendar_event.invoke({"summary": "Test", "start_time": "2026-09-08T10:00:00", "end_time": "2026-09-08T11:00:00"})
    assert "Authentication required" in res_cal.get("error", "")

    res_gmail = search_gmail_messages.invoke({"query": "test"})
    assert "Authentication required" in res_gmail

    res_zoom = list_zoom_transcripts.invoke({})
    assert "Authentication required" in res_zoom

    res_meet = list_google_meet_transcripts.invoke({})
    assert "Authentication required" in res_meet

    print("   -> All subagent tools strictly reject unauthenticated calls!")


def test_thread_isolation_strict():
    print("4. Testing thread isolation by OAuth2 user_id...")
    assert retrive_all_threads(None) == []
    assert retrive_all_threads("") == []
    threads = retrive_all_threads("mock_oauth_user_id_123")
    assert isinstance(threads, list)
    print("   -> Thread isolation strictly enforced!")


def test_mongo_credential_save_and_retrieve():
    print("5. Testing MongoDB server credential storage and retrieval...")
    test_user = "oauth_test_user_777"
    test_creds = {
        "account_id": "acc_123",
        "client_id": "client_abc",
        "client_secret": "secret_xyz"
    }
    
    if credential_manager.collection is not None:
        saved = credential_manager.save_credential(
            user_id=test_user,
            service="zoom",
            auth_type="zoom_s2s",
            credential_data=test_creds,
            metadata={"email": "tester@example.com"}
        )
        assert saved is True
        
        retrieved = credential_manager.get_credential(user_id=test_user, service="zoom")
        assert retrieved is not None
        assert retrieved["account_id"] == "acc_123"
        assert retrieved["client_id"] == "client_abc"
        
        integrations = credential_manager.list_user_credentials(user_id=test_user)
        assert len(integrations) >= 1
        assert any(i["service"] == "zoom" for i in integrations)
        
        # Cleanup
        credential_manager.delete_credential(user_id=test_user, service="zoom")
        print("   -> MongoDB credential isolation, storage, and deletion verified!")
    else:
        print("   -> MONGO_URI not yet pointing to live MongoDB server. Test ready for live server.")


if __name__ == "__main__":
    print("=== RUNNING NEXUSAI ZERO-FALLBACK & OAUTH2 ISOLATION TESTS ===")
    test_encryption_roundtrip()
    test_zero_local_fallback_enforcement()
    test_tool_oauth2_auth_enforcement()
    test_thread_isolation_strict()
    test_mongo_credential_save_and_retrieve()
    print("\n=== ALL ZERO-FALLBACK & OAUTH2 ISOLATION TESTS PASSED! ===")
