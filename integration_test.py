"""
Integration test: Verify session_store works with backend API
"""
import sys
sys.path.insert(0, 'backend')

from app.services.session_store import create_session, get_session
from app.schemas.debate import (
    StartSessionRequest, DebateTurnRequest
)

print("=" * 60)
print("  INTEGRATION TEST: session_store ↔ backend API")
print("=" * 60)

# Test 1: create_session (API wrapper)
print("\n[1] Testing create_session()...")
session = create_session(
    topic="Học sinh có nên dùng AI?",
    stance="Ủng hộ",
    difficulty="Trung bình",
    input_mode="text"
)

assert isinstance(session, dict), "Session should be a dict"
assert "session_id" in session, "Session should have session_id"
assert session["topic"] == "Học sinh có nên dùng AI?", "Topic should match"
assert session["stance"] == "Ủng hộ", "Stance should match"
assert session["status"] == "active", "Status should be 'active'"
print(f"✓ Created session: {session['session_id'][:8]}...")

# Test 2: get_session (API wrapper)
print("\n[2] Testing get_session()...")
retrieved = get_session(session["session_id"])

assert retrieved is not None, "Session should be retrieved"
assert isinstance(retrieved, dict), "Retrieved session should be a dict"
assert retrieved["session_id"] == session["session_id"], "Session IDs should match"
assert retrieved["topic"] == session["topic"], "Topics should match"
print(f"✓ Retrieved session: {retrieved['session_id'][:8]}...")

# Test 3: Pydantic models
print("\n[3] Testing Pydantic models...")
req = StartSessionRequest(
    topic="Test",
    stance="Phản đối",
    difficulty="Cơ bản",
    input_mode="text"
)
assert req.topic == "Test", "Pydantic model should work"
print(f"✓ Pydantic model validation works")

turn_req = DebateTurnRequest(
    session_id=session["session_id"],
    user_argument="Test argument"
)
assert turn_req.session_id == session["session_id"], "Turn request should work"
print(f"✓ DebateTurnRequest validation works")

print("\n" + "=" * 60)
print("  ✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nSession store is now compatible with backend API!")
