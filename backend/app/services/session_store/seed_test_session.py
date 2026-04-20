"""
AI Debate Trainer — Test Session Seeder v2
Dùng đúng Pydantic models từ debate.py:
  StartSessionRequest → start_session()  → StartSessionResponse
  DebateTurnRequest   → process_turn()   → DebateTurnResponse
  end_session()                          → SessionInfoResponse
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import create_tables
from app.schemas.debate import StartSessionRequest, DebateTurnRequest
from repository import (
    start_session, get_session_info, end_session,
    process_turn, save_cer_score, save_feedback,
    save_content_flag, get_progress_summary,
)


# ──────────────────────────────────────────────────────
#  DỮ LIỆU MẪU — khớp với field names trong debate.py
# ──────────────────────────────────────────────────────

SESSION_INPUT = StartSessionRequest(
    topic      = "Học sinh có nên dùng AI để hỗ trợ học tập?",
    stance     = "Ủng hộ",
    difficulty = "Trung bình",
    input_mode = "text",
)

TURNS_DATA = [
    {
        "req": DebateTurnRequest(
            session_id    = "",   # sẽ gán sau khi có session_id
            user_argument = (
                "Em nghĩ AI giúp học sinh học nhanh hơn vì có thể giải thích lại "
                "kiến thức theo nhiều cách, giúp các bạn không hiểu bài có thể tự "
                "ôn tập ở nhà mà không cần chờ hỏi thầy cô."
            ),
        ),
        "ai_rebuttal": (
            "Bạn nêu lợi ích thực tế, nhưng nếu học sinh quen phụ thuộc AI để giải "
            "thích mọi thứ, liệu các em có mất khả năng tự vật lộn với bài khó — "
            "điều rèn tư duy sâu hơn? Bạn có ví dụ AI giúp ích mà không tạo lệ thuộc?"
        ),
        "processing_ms": 2850,
        "claim": 8.0, "evidence": 4.5, "reasoning": 6.0,
        "strengths":   ["Luận điểm rõ ràng, dễ hiểu"],
        "weaknesses":  ["Chưa có số liệu hay ví dụ cụ thể"],
        "suggestions": ["Thêm 1 nghiên cứu về kết quả học tập khi dùng AI"],
    },
    {
        "req": DebateTurnRequest(
            session_id    = "",
            user_argument = (
                "Theo nghiên cứu MIT năm 2023, học sinh dùng AI như gia sư cá nhân "
                "tăng điểm trung bình 15% so với nhóm không dùng — đó là bằng chứng "
                "tác động tích cực rõ ràng, không chỉ là cảm tính."
            ),
        ),
        "ai_rebuttal": (
            "Dẫn chứng MIT là bước tiến tốt. Nhưng nghiên cứu đó đo kết quả ngắn hạn "
            "hay dài hạn? Học sinh có thể đạt điểm cao nhờ AI nhắc đáp án, nhưng sau "
            "6 tháng không dùng AI, kiến thức còn lại bao nhiêu?"
        ),
        "processing_ms": 3100,
        "claim": 8.5, "evidence": 8.0, "reasoning": 7.5,
        "strengths":   ["Có dẫn chứng cụ thể từ nghiên cứu uy tín", "Số liệu rõ ràng"],
        "weaknesses":  ["Chưa phân tích giới hạn của nghiên cứu"],
        "suggestions": ["Bổ sung thông tin về độ bền kiến thức dài hạn"],
    },
    {
        "req": DebateTurnRequest(
            session_id    = "",
            user_argument = (
                "Lệ thuộc hay không phụ thuộc vào cách giáo viên hướng dẫn. "
                "Nếu thầy cô dạy học sinh dùng AI để đặt câu hỏi và kiểm tra suy "
                "nghĩ của mình, AI trở thành công cụ rèn tư duy phản biện, "
                "không phải công cụ lười biếng."
            ),
        ),
        "ai_rebuttal": (
            "Lập luận thuyết phục hơn vì đã chuyển trọng tâm sang vai trò giáo viên. "
            "Tuy nhiên, có bao nhiêu giáo viên Việt Nam được đào tạo để hướng dẫn AI "
            "một cách sư phạm? Nếu hạ tầng chưa sẵn sàng, lợi ích bạn nêu "
            "có thể chỉ là lý thuyết."
        ),
        "processing_ms": 2700,
        "claim": 9.0, "evidence": 6.5, "reasoning": 8.5,
        "strengths":   ["Phản hồi trực tiếp điểm yếu từ lượt trước", "Lập luận sâu"],
        "weaknesses":  ["Chưa có bằng chứng về mô hình triển khai thành công"],
        "suggestions": ["Dẫn ví dụ quốc gia đã áp dụng AI sư phạm thành công"],
    },
]


# ──────────────────────────────────────────────────────
#  RUNNER
# ──────────────────────────────────────────────────────

def run_test_session():
    print("\n" + "═" * 62)
    print("  AI DEBATE TRAINER v2 — TEST SESSION")
    print("═" * 62)

    # 1. Khởi tạo schema
    create_tables()

    # ── BƯỚC 1: start_session ──────────────────────────────
    # Input : StartSessionRequest
    # Output: StartSessionResponse
    session_resp = start_session(SESSION_INPUT)

    print(f"\n[StartSessionResponse]")
    print(f"  session_id : {session_resp.session_id[:8]}...")
    print(f"  topic      : {session_resp.topic}")
    print(f"  stance     : {session_resp.stance}")
    print(f"  difficulty : {session_resp.difficulty}")
    print(f"  input_mode : {session_resp.input_mode}")
    print(f"  status     : {session_resp.status}")

    sid = session_resp.session_id

    # ── BƯỚC 2: process_turn (vòng lặp tranh biện) ─────────
    # Input : DebateTurnRequest
    # Output: DebateTurnResponse
    for i, t in enumerate(TURNS_DATA, start=1):
        # Gán session_id thực vào request
        turn_req = DebateTurnRequest(
            session_id    = sid,
            user_argument = t["req"].user_argument,
        )

        turn_resp = process_turn(
            req                = turn_req,
            ai_rebuttal        = t["ai_rebuttal"],
            processing_time_ms = t["processing_ms"],
            is_safe            = True,
        )

        print(f"\n  {'─'*56}")
        print(f"  [DebateTurnResponse] lượt {i}")
        print(f"  {'─'*56}")
        print(f"  session_id    : {turn_resp.session_id[:8]}...")
        print(f"  user_argument : {turn_resp.user_argument[:65]}...")
        print(f"  ai_rebuttal   : {turn_resp.ai_rebuttal[:65]}...")
        print(f"  status        : {turn_resp.status}")
        print(f"  ⏱  {t['processing_ms']} ms")

        # Lưu CER score & feedback (nội bộ — không expose qua Pydantic)
        turn_id = save_cer_score(sid, t["claim"], t["evidence"], t["reasoning"])
        save_feedback(turn_id, t["strengths"], t["weaknesses"], t["suggestions"])
        save_content_flag(turn_id, is_flagged=False)

        total = round((t["claim"] + t["evidence"] + t["reasoning"]) / 3, 2)
        print(f"  📊 Claim {t['claim']} | Evidence {t['evidence']} | Reasoning {t['reasoning']} → {total}")

    # ── BƯỚC 3: end_session ────────────────────────────────
    # Output: SessionInfoResponse
    final = end_session(sid)

    print(f"\n  {'─'*56}")
    print(f"  [SessionInfoResponse] — kết thúc phiên")
    print(f"  {'─'*56}")
    print(f"  session_id : {final.session_id[:8]}...")
    print(f"  topic      : {final.topic}")
    print(f"  stance     : {final.stance}")
    print(f"  difficulty : {final.difficulty}")
    print(f"  input_mode : {final.input_mode}")
    print(f"  status     : {final.status}")

    # ── BƯỚC 4: Progress dashboard ─────────────────────────
    progress = get_progress_summary()
    print(f"\n{'═'*62}")
    print(f"  PROGRESS DASHBOARD")
    print(f"{'═'*62}")
    print(f"  Phiên hoàn thành : {progress['total_sessions']}")
    for k, v in progress["average_scores"].items():
        bar = "█" * int(v) + "░" * (10 - int(v))
        print(f"  {k:12s}: [{bar}] {v:.2f}")

    print(f"\n  ✅ DB : debate_trainer_v2.db\n")


if __name__ == "__main__":
    run_test_session()
