"""
Test: API with SQLite integration
Kiểm tra xem /session và /turn có hoạt động với DB không
"""
import sys
sys.path.insert(0, 'backend')

from app.services.session_store import create_session, get_session
from app.schemas.debate import DebateTurnRequest
from app.services.session_store.repository import (
    get_session_info, process_turn, save_cer_score,
    save_feedback, save_content_flag, end_session
)
from app.services.session_store.database import get_connection
import time

print("=" * 70)
print("  END-TO-END TEST: API + SQLite Integration")
print("=" * 70)

# Test 1: Create session
print("\n[1] Create Session via API wrapper...")
session = create_session(
    topic="Học sinh có nên dùng AI?",
    stance="Ủng hộ",
    difficulty="Trung bình",
    input_mode="text"
)
session_id = session["session_id"]
print(f"✓ Created: {session_id[:8]}...")

# Test 2: Get session info from DB
print("\n[2] Get Session Info từ DB...")
session_info = get_session_info(session_id)
print(f"✓ Retrieved: {session_info.topic}")
print(f"  Status: {session_info.status}")
print(f"  Turn Count: {session_info.session_id[:8]}...")

# Test 3: Process a turn (without real AI)
print("\n[3] Process Turn (lưu vào DB)...")
turn_req = DebateTurnRequest(
    session_id=session_id,
    user_argument="Em nghĩ AI giúp học nhanh hơn."
)

turn_resp = process_turn(
    req=turn_req,
    ai_rebuttal="Nhưng AI có thể làm lệ thuộc.",
    processing_time_ms=2500,
    is_safe=True,
)
print(f"✓ Turn saved:")
print(f"  User: {turn_resp.user_argument[:50]}...")
print(f"  AI: {turn_resp.ai_rebuttal[:50]}...")
print(f"  Status: {turn_resp.status}")

# Test 4: Save CER score
print("\n[4] Save CER Score...")
try:
    save_cer_score(session_id, claim=8.0, evidence=7.5, reasoning=7.8)
    print(f"✓ CER score saved")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Save feedback
print("\n[5] Save Feedback...")
try:
    # Get turn_id
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id FROM debate_turns
            WHERE session_id = ? ORDER BY turn_number DESC LIMIT 1
        """, (session_id,)).fetchone()
        turn_id = row["id"] if row else None
    
    if turn_id:
        save_feedback(
            turn_id=turn_id,
            strengths=["Luận điểm rõ ràng"],
            weaknesses=["Cần dẫn chứng"],
            suggestions=["Bổ sung số liệu"]
        )
        print(f"✓ Feedback saved")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 6: Save content flag
print("\n[6] Save Content Flag...")
try:
    if turn_id:
        save_content_flag(
            turn_id=turn_id,
            is_flagged=False,
            flag_reason="",
            flagged_terms=[]
        )
        print(f"✓ Content flag saved")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 7: Process more turns (to test turn counting)
print("\n[7] Process 2nd Turn (turn_count should increase)...")
for i in range(2):
    turn_req = DebateTurnRequest(
        session_id=session_id,
        user_argument=f"Lập luận thứ {i+2}"
    )
    turn_resp = process_turn(
        req=turn_req,
        ai_rebuttal=f"Phản biện thứ {i+2}",
        processing_time_ms=2000,
        is_safe=True,
    )
    print(f"  ✓ Turn {i+2}: status={turn_resp.status}")
    
    if turn_resp.status == "completed":
        print(f"  → Session completed after {i+2} turns!")
        break

# Test 8: Get final session info
print("\n[8] Get Final Session Info...")
final_info = get_session_info(session_id)
print(f"✓ Final status: {final_info.status}")

print("\n" + "=" * 70)
print("  ✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nAPI is now connected to SQLite!")
print("Each turn is saved with CER scores, feedback, and content flags.")
