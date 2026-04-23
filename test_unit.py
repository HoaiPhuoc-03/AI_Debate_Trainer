"""
Unit Tests for Session Store Functions
Tests individual functions without calling the full API
"""
import sys
sys.path.insert(0, 'backend')

from app.services.session_store import create_session, get_session
from app.schemas.debate import StartSessionRequest, DebateTurnRequest, SessionInfoResponse

print("=" * 70)
print("  UNIT TESTS: Session Store Functions")
print("=" * 70)

# Test 1: create_session wrapper
print("\n[TEST 1] create_session() - wrapper function")
print("-" * 70)
try:
    session = create_session(
        topic="Học sinh có nên dùng AI?",
        stance="Ủng hộ",
        difficulty="Cơ bản",
        input_mode="text"
    )
    
    # Verify return type and structure
    assert isinstance(session, dict), "Should return dict"
    assert "session_id" in session, "Must have session_id"
    assert "topic" in session, "Must have topic"
    assert "stance" in session, "Must have stance"
    assert "difficulty" in session, "Must have difficulty"
    assert "input_mode" in session, "Must have input_mode"
    assert "status" in session, "Must have status"
    
    # Verify values
    assert session["topic"] == "Học sinh có nên dùng AI?"
    assert session["stance"] == "Ủng hộ"
    assert session["difficulty"] == "Cơ bản"
    assert session["input_mode"] == "text"
    assert session["status"] in ["active", "ready"], "Status should be active or ready"
    
    session_id = session["session_id"]
    print(f"✓ PASS: Session created with ID {session_id[:8]}...")
    print(f"  - Topic: {session['topic']}")
    print(f"  - Stance: {session['stance']}")
    print(f"  - Status: {session['status']}")
    
except Exception as e:
    print(f"✗ FAIL: {str(e)}")
    sys.exit(1)

# Test 2: get_session wrapper
print("\n[TEST 2] get_session() - wrapper function")
print("-" * 70)
try:
    retrieved = get_session(session_id)
    
    # Verify return type
    assert retrieved is not None, "Should find the session"
    assert isinstance(retrieved, dict), "Should return dict"
    
    # Verify structure
    assert retrieved["session_id"] == session_id, "Session ID should match"
    assert retrieved["topic"] == session["topic"], "Topic should match"
    assert retrieved["stance"] == session["stance"], "Stance should match"
    
    print(f"✓ PASS: Session retrieved with ID {retrieved['session_id'][:8]}...")
    print(f"  - Topic: {retrieved['topic']}")
    print(f"  - Stance: {retrieved['stance']}")
    print(f"  - Difficulty: {retrieved['difficulty']}")
    
except Exception as e:
    print(f"✗ FAIL: {str(e)}")
    sys.exit(1)

# Test 3: Non-existent session
print("\n[TEST 3] get_session() - non-existent session")
print("-" * 70)
try:
    result = get_session("fake-session-id-12345")
    
    # Should return None for non-existent session
    assert result is None, "Should return None for non-existent session"
    
    print(f"✓ PASS: Correctly returns None for non-existent session")
    
except Exception as e:
    print(f"✗ FAIL: {str(e)}")
    sys.exit(1)

# Test 4: Pydantic models
print("\n[TEST 4] Pydantic models validation")
print("-" * 70)
try:
    # Valid request
    req = StartSessionRequest(
        topic="Test",
        stance="Phản đối",
        difficulty="Nâng cao",
        input_mode="text"
    )
    assert req.topic == "Test", "Topic should be set"
    print(f"✓ PASS: StartSessionRequest validation works")
    
    # Valid turn request
    turn_req = DebateTurnRequest(
        session_id=session_id,
        user_argument="This is a test argument"
    )
    assert turn_req.session_id == session_id, "Session ID should be set"
    assert turn_req.user_argument == "This is a test argument", "Argument should be set"
    print(f"✓ PASS: DebateTurnRequest validation works")
    
    # Valid response
    resp = SessionInfoResponse(
        session_id="test-id",
        topic="Test",
        stance="Ủng hộ",
        difficulty="Cơ bản",
        input_mode="text",
        status="active"
    )
    assert resp.session_id == "test-id", "Session ID should be set"
    print(f"✓ PASS: SessionInfoResponse validation works")
    
except Exception as e:
    print(f"✗ FAIL: {str(e)}")
    sys.exit(1)

# Test 5: Multiple sessions
print("\n[TEST 5] Multiple sessions support")
print("-" * 70)
try:
    sessions = []
    for i in range(3):
        s = create_session(
            topic=f"Topic {i}",
            stance="Ủng hộ",
            difficulty="Trung bình",
            input_mode="text"
        )
        sessions.append(s)
    
    # Verify all are unique
    ids = [s["session_id"] for s in sessions]
    assert len(ids) == len(set(ids)), "All session IDs should be unique"
    
    # Verify all can be retrieved
    for s in sessions:
        retrieved = get_session(s["session_id"])
        assert retrieved is not None, f"Should find session {s['session_id']}"
        assert retrieved["topic"] == s["topic"], f"Topic should match for {s['session_id']}"
    
    print(f"✓ PASS: Created and retrieved {len(sessions)} unique sessions")
    
except Exception as e:
    print(f"✗ FAIL: {str(e)}")
    sys.exit(1)

print("\n" + "=" * 70)
print("  ✅ ALL UNIT TESTS PASSED!")
print("=" * 70)
print("\nSummary:")
print("  ✓ create_session() works correctly")
print("  ✓ get_session() works correctly")
print("  ✓ Pydantic models validate properly")
print("  ✓ Multiple sessions are supported")
print("  ✓ Session persistence works")
