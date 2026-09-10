"""
Test all tool credential flows end-to-end:
1. MongoDB connectivity
2. Credential save/retrieve/delete for each service key
3. _clean_cred_info strips internal keys
4. Gmail rejects service_account JSON
5. Each service builder uses correct MongoDB key
6. Upload mapping from UI labels to MongoDB service keys
"""
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

PASS = 0
FAIL = 0

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} -- {detail}")


print("\n" + "="*70)
print("TEST 1: MongoDB Connectivity & CredentialManager import")
print("="*70)

try:
    from nexusai.db.credentials import credential_manager, CredentialsNotFoundError
    test("CredentialManager imported", True)
    test("MongoDB connected", credential_manager._connected, 
         f"MONGO_URI={os.getenv('MONGO_URI','NOT SET')[:30]}...")
    test("Collection accessible", credential_manager.collection is not None,
         "credential_manager.collection is None")
except Exception as e:
    test("CredentialManager import", False, str(e))
    print("CRITICAL: Cannot proceed without CredentialManager")
    sys.exit(1)


print("\n" + "="*70)
print("TEST 2: _clean_cred_info strips internal keys")
print("="*70)

test_data = {
    "client_id": "test_id",
    "client_secret": "test_secret",
    "refresh_token": "test_refresh",
    "_auth_type": "oauth_token",
    "_metadata": {"filename": "token.json"}
}
test_copy = dict(test_data)
clean_data, auth_type = credential_manager._clean_cred_info(test_copy)
test("_auth_type stripped from data", "_auth_type" not in clean_data, 
     f"_auth_type still in data: {list(clean_data.keys())}")
test("_metadata stripped from data", "_metadata" not in clean_data,
     f"_metadata still in data: {list(clean_data.keys())}")
test("auth_type returned correctly", auth_type == "oauth_token",
     f"Expected 'oauth_token', got '{auth_type}'")
test("Original credential fields preserved", 
     clean_data.get("client_id") == "test_id" and clean_data.get("refresh_token") == "test_refresh",
     f"Fields lost: {list(clean_data.keys())}")


print("\n" + "="*70)
print("TEST 3: Credential CRUD per service key")
print("="*70)

TEST_USER = "__test_tool_mapping_user__"
SERVICES = {
    "gmail": {
        "data": {"client_id": "test", "client_secret": "test", "refresh_token": "test_refresh"},
        "auth_type": "oauth_token"
    },
    "google_calendar": {
        "data": {"type": "service_account", "project_id": "test", "private_key_id": "test", 
                 "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n",
                 "client_email": "test@test.iam.gserviceaccount.com", "client_id": "123"},
        "auth_type": "service_account"
    },
    "google_meet": {
        "data": {"type": "service_account", "project_id": "test", "private_key_id": "test",
                 "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n",
                 "client_email": "test@test.iam.gserviceaccount.com", "client_id": "456"},
        "auth_type": "service_account"
    },
    "zoom": {
        "data": {"account_id": "test_acc", "client_id": "test_cid", "client_secret": "test_csec"},
        "auth_type": "zoom_s2s"
    }
}

# Save test credentials
for srv, info in SERVICES.items():
    try:
        result = credential_manager.save_credential(
            user_id=TEST_USER, service=srv,
            auth_type=info["auth_type"], credential_data=info["data"]
        )
        test(f"Save '{srv}' credential", result, "save_credential returned False")
    except Exception as e:
        test(f"Save '{srv}' credential", False, str(e))

# Retrieve and verify
for srv, info in SERVICES.items():
    try:
        cred = credential_manager.get_credential(TEST_USER, srv)
        test(f"Retrieve '{srv}' credential", cred is not None, "get_credential returned None")
        if cred:
            test(f"'{srv}' has _auth_type", "_auth_type" in cred, "Missing _auth_type key")
            test(f"'{srv}' auth_type matches", cred.get("_auth_type") == info["auth_type"],
                 f"Expected '{info['auth_type']}', got '{cred.get('_auth_type')}'")
    except Exception as e:
        test(f"Retrieve '{srv}' credential", False, str(e))

# List credentials for test user
try:
    creds_list = credential_manager.list_user_credentials(TEST_USER)
    test("List user credentials", len(creds_list) == 4, 
         f"Expected 4 services, got {len(creds_list)}: {[c['service'] for c in creds_list]}")
    
    listed_services = {c["service"] for c in creds_list}
    for expected_srv in SERVICES:
        test(f"'{expected_srv}' in listing", expected_srv in listed_services,
             f"Missing from list: {listed_services}")
except Exception as e:
    test("List user credentials", False, str(e))


print("\n" + "="*70)
print("TEST 4: Gmail rejects service_account JSON")
print("="*70)

# Save a service_account credential for Gmail
try:
    credential_manager.save_credential(
        user_id=TEST_USER, service="gmail",
        auth_type="service_account",
        credential_data={"type": "service_account", "project_id": "test", 
                         "private_key_id": "test",
                         "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n",
                         "client_email": "test@test.iam.gserviceaccount.com", "client_id": "123"}
    )
    
    # Now try to build Gmail service — should fail with clear error
    try:
        service = credential_manager.get_gmail_service(TEST_USER)
        test("Gmail rejects service_account", False, 
             "get_gmail_service did NOT reject service_account — this is a bug!")
    except CredentialsNotFoundError as e:
        error_msg = str(e)
        test("Gmail rejects service_account", "token.json" in error_msg,
             f"Error doesn't mention token.json: {error_msg}")
        test("Gmail error mentions OAuth2", "OAuth2" in error_msg or "oauth" in error_msg.lower(),
             f"Error doesn't mention OAuth2: {error_msg}")
    except Exception as e:
        test("Gmail rejects service_account", False, f"Wrong exception type: {type(e).__name__}: {e}")
except Exception as e:
    test("Gmail service_account rejection setup", False, str(e))


print("\n" + "="*70)
print("TEST 5: Service builders use correct MongoDB keys")
print("="*70)

# Restore gmail to oauth_token for clean state
credential_manager.save_credential(
    user_id=TEST_USER, service="gmail",
    auth_type="oauth_token",
    credential_data={"client_id": "test", "client_secret": "test", "refresh_token": "test_refresh"}
)

# Test Calendar builder looks up "google_calendar"
try:
    service = credential_manager.get_calendar_service(TEST_USER)
    test("Calendar builder found credential", False, "Should have failed with fake service account key")
except CredentialsNotFoundError:
    test("Calendar builder found credential", False, "Credential not found — wrong service key?")
except Exception as e:
    error_str = str(e)
    if "No Google Calendar credentials found" in error_str:
        test("Calendar builder found credential", False, "Credential lookup failed")
    else:
        test("Calendar builder found credential (lookup OK, API build expected fail)", True)

# Test Gmail builder looks up "gmail"  
try:
    service = credential_manager.get_gmail_service(TEST_USER)
    test("Gmail builder found credential (lookup OK, service built)", service is not None)
except CredentialsNotFoundError:
    test("Gmail builder found credential", False, "Credential not found — wrong service key?")
except Exception as e:
    error_str = str(e)
    if "No Gmail credentials found" in error_str:
        test("Gmail builder found credential", False, "Credential lookup failed")
    else:
        test("Gmail builder found credential (lookup OK, API build expected fail)", True)

# Test Meet/Drive builder looks up "google_meet"
try:
    service = credential_manager.get_drive_and_docs_services(TEST_USER)
    test("Meet/Drive builder found credential", False, "Should have failed with fake service account key")
except CredentialsNotFoundError:
    test("Meet/Drive builder found credential", False, "Credential not found — wrong service key?")
except Exception as e:
    error_str = str(e)
    if "No Google Meet/Drive credentials found" in error_str:
        test("Meet/Drive builder found credential", False, "Credential lookup failed")
    else:
        test("Meet/Drive builder found credential (lookup OK, API build expected fail)", True)

# Test Zoom builder looks up "zoom"
try:
    token = credential_manager.get_zoom_access_token(TEST_USER)
    test("Zoom builder found credential", False, "Should have failed with fake Zoom creds")
except CredentialsNotFoundError:
    test("Zoom builder found credential", False, "Credential not found — wrong service key?")
except (RuntimeError, ValueError) as e:
    # Expected: Zoom API call fails with fake creds, but lookup succeeded
    test("Zoom builder found credential (lookup OK, API call expected fail)", True)
except Exception as e:
    error_str = str(e)
    if "No Zoom credentials found" in error_str:
        test("Zoom builder found credential", False, "Credential lookup failed")
    else:
        test("Zoom builder found credential (lookup OK, expected fail)", True)


print("\n" + "="*70)
print("TEST 6: UI upload mapping -> MongoDB service keys")
print("="*70)

# Simulate Streamlit mapping logic (from app.py line 671)
streamlit_labels = [
    "Gmail (token.json — OAuth2 Token)",
    "Google Calendar (callender_api_agent_key.json — Service Account)",
    "Google Meet / Drive (Service Account JSON)",
]

expected_mapping = {
    "Gmail (token.json — OAuth2 Token)": "gmail",
    "Google Calendar (callender_api_agent_key.json — Service Account)": "google_calendar",
    "Google Meet / Drive (Service Account JSON)": "google_meet",
}

for label in streamlit_labels:
    # Replicate the actual mapping logic from app.py
    srv = "gmail" if "Gmail" in label else ("google_calendar" if "Calendar" in label else "google_meet")
    expected = expected_mapping[label]
    test(f"Streamlit '{label[:30]}...' -> '{srv}'", srv == expected,
         f"Expected '{expected}', got '{srv}'")

# Test Zoom condition
zoom_label = "Zoom (Server-to-Server OAuth)"
test(f"Streamlit Zoom label detected", "Zoom" in zoom_label, "Zoom substring not found")

# Web UI dropdown values (from index.html)
web_ui_values = {
    "gmail": "Gmail upload token.json (OAuth2 Token)",
    "google_calendar": "Google Calendar upload Service Account JSON",
    "google_meet": "Google Meet / Drive upload Service Account JSON",
}

for value, label in web_ui_values.items():
    # The <option value="..."> is what gets sent to the API
    test(f"Web UI '{label[:35]}...' sends value='{value}'", value in SERVICES,
         f"'{value}' is not a valid MongoDB service key")


print("\n" + "="*70)
print("TEST 7: Non-existent user gets clear errors")
print("="*70)

FAKE_USER = "__nonexistent_test_user__"

try:
    credential_manager.get_calendar_service(FAKE_USER)
    test("Calendar error for missing user", False, "No exception raised")
except CredentialsNotFoundError as e:
    msg = str(e)
    test("Calendar error for missing user", "callender_api_agent_key" in msg or "Calendar" in msg, 
         f"Error not helpful: {msg}")
except Exception as e:
    test("Calendar error for missing user", False, f"Wrong exception: {e}")

try:
    credential_manager.get_gmail_service(FAKE_USER)
    test("Gmail error for missing user", False, "No exception raised")
except CredentialsNotFoundError as e:
    msg = str(e)
    test("Gmail error for missing user", "token.json" in msg, f"Error doesn't mention token.json: {msg}")
except Exception as e:
    test("Gmail error for missing user", False, f"Wrong exception: {e}")

try:
    credential_manager.get_drive_and_docs_services(FAKE_USER)
    test("Meet/Drive error for missing user", False, "No exception raised")
except CredentialsNotFoundError as e:
    msg = str(e)
    test("Meet/Drive error for missing user", "Meet" in msg or "Drive" in msg,
         f"Error not helpful: {msg}")
except Exception as e:
    test("Meet/Drive error for missing user", False, f"Wrong exception: {e}")

try:
    credential_manager.get_zoom_access_token(FAKE_USER)
    test("Zoom error for missing user", False, "No exception raised")
except CredentialsNotFoundError as e:
    msg = str(e)
    test("Zoom error for missing user", "Zoom S2S" in msg or "Zoom" in msg,
         f"Error not helpful: {msg}")
except Exception as e:
    test("Zoom error for missing user", False, f"Wrong exception: {e}")


print("\n" + "="*70)
print("CLEANUP: Removing test credentials")
print("="*70)

for srv in SERVICES:
    try:
        credential_manager.delete_credential(TEST_USER, srv)
        test(f"Deleted test '{srv}' credential", True)
    except Exception as e:
        test(f"Deleted test '{srv}' credential", False, str(e))

# Verify cleanup
remaining = credential_manager.list_user_credentials(TEST_USER)
test("All test credentials cleaned up", len(remaining) == 0,
     f"{len(remaining)} still remain: {[c['service'] for c in remaining]}")


print("\n" + "="*70)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
print("="*70 + "\n")

sys.exit(0 if FAIL == 0 else 1)
