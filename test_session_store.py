import sys
sys.path.insert(0, 'backend')

from app.services.session_store import create_session, get_session

# Test create_session
session = create_session(
    topic="Test topic",
    stance="Ủng hộ",
    difficulty="Cơ bản",
    input_mode="text"
)

print(f"✓ Created session: {session['session_id'][:8]}...")
print(f"  Topic: {session['topic']}")
print(f"  Stance: {session['stance']}")
print(f"  Status: {session['status']}")

# Test get_session
retrieved = get_session(session['session_id'])
if retrieved:
    print(f"✓ Retrieved session: {retrieved['session_id'][:8]}...")
    print(f"  Topic: {retrieved['topic']}")
else:
    print("✗ Failed to retrieve session")
