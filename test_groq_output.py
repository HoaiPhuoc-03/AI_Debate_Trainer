#!/usr/bin/env python3
"""Extensive test script to verify raw Groq output for various cases."""

import sys
import json
import io
import re
import time

# Force UTF-8 output in Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, "c:\\Users\\phong\\AI_Debate_Trainer\\backend")

from app.core.config import settings
from app.services.prompt_builder import build_cer_messages
from app.services.groq_client import call_groq as groq_call

# Unicode ranges for Chinese characters (CJK)
CHINESE_CHAR_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')

test_cases = [
    {
        "name": "Social Media (Free Mode)",
        "mode": "free_debate",
        "topic": "Mạng xã hội có hại cho xã hội",
        "stance": "support",
        "difficulty": "intermediate",
        "user_argument": "Mạng xã hội làm tăng tỷ lệ trầm cảm ở thanh thiếu niên lên 50% theo báo cáo của Hiệp hội Tâm lý học Hoa Kỳ (APA).",
        "has_evidence": True,
    },
    {
        "name": "AI in Education (Free Mode)",
        "mode": "free_debate",
        "topic": "Cho phép học sinh sử dụng AI trong học tập",
        "stance": "oppose",
        "difficulty": "advanced",
        "user_argument": "Học sinh sử dụng AI quá nhiều sẽ mất đi tư duy phản biện và khả năng viết lách, do tất cả bài tập đều do AI làm hộ.",
        "has_evidence": False,
    },
    {
        "name": "Working While Studying (Full Argument Mode)",
        "mode": "full_argument",
        "topic": "Sinh viên đại học đi làm thêm từ năm nhất",
        "stance": "support",
        "difficulty": "intermediate",
        "user_argument": "Nghiên cứu của Harvard 2022 cho thấy đi làm thêm giúp sinh viên phát triển kỹ năng quản lý thời gian và sớm có kinh nghiệm làm việc thực tế.",
        "has_evidence": True,
    },
    {
        "name": "Renewable Energy (Free Mode)",
        "mode": "free_debate",
        "topic": "Chuyển dịch hoàn toàn sang năng lượng tái tạo",
        "stance": "support",
        "difficulty": "intermediate",
        "user_argument": "Năng lượng gió và mặt trời ngày càng rẻ, theo báo cáo IRENA 2023 chi phí sản xuất điện mặt trời giảm 89% trong thập kỷ qua.",
        "has_evidence": True,
    },
    {
        "name": "Fake NASA Evidence (Free Mode)",
        "mode": "free_debate",
        "topic": "Cho phép học sinh sử dụng AI trong học tập",
        "stance": "oppose",
        "difficulty": "intermediate",
        "user_argument": "Theo báo cáo chính thức của cơ quan hàng không vũ trụ NASA năm 2025, 99% học sinh trung học sử dụng AI để làm hộ bài tập đều bị mất khả năng viết lách hoàn toàn.",
        "has_evidence": True,
        "expect_fake": True,
    }
]

print("=" * 80)
print("STARTING EXTENSIVE LIVE VERIFICATION TESTING")
print("=" * 80)

success_count = 0

for idx, case in enumerate(test_cases, 1):
    if idx > 1:
        print("Sleeping 20 seconds to avoid Groq rate limits...")
        time.sleep(20)
    print(f"\n[Test Case {idx}] {case['name']}")
    print("-" * 50)
    print(f"Topic: {case['topic']}")
    print(f"Stance: {case['stance']} | Mode: {case['mode']}")
    print(f"User Argument: {case['user_argument']}")
    
    # Fetch search context before building messages
    try:
        from app.services.search_service import get_combined_search_context
        user_search_context, ai_search_context = get_combined_search_context(case['user_argument'], case['topic'], case['stance'])
    except Exception:
        user_search_context = ""
        ai_search_context = ""

    # Build messages
    messages = build_cer_messages(
        topic=case['topic'],
        stance=case['stance'],
        difficulty=case['difficulty'],
        user_argument=case['user_argument'],
        mode=case['mode'],
        language="vi",
        user_search_context=user_search_context,
        ai_search_context=ai_search_context
    )
    
    print("Calling Groq...")
    retries = 4
    delay = 12
    result = {"ok": False, "error": "Not started"}
    for attempt in range(retries + 1):
        result = groq_call(messages, max_tokens=1500, temperature=0.3)
        if result['ok']:
            break
        error_msg = str(result.get('error') or '')
        if "429" in error_msg and attempt < retries:
            print(f"  Got 429 Rate Limit. Retrying in {delay} seconds (attempt {attempt+1}/{retries})...")
            time.sleep(delay)
            delay *= 2
        else:
            break
            
    if not result['ok']:
        print(f"✗ Call failed: {result.get('error')}")
        continue
        
    print("✓ Response received.")
    raw_text = result['text'].strip()
    
    # Try parsing
    try:
        # Strip codeblock wrappers if present
        json_text = raw_text
        if json_text.startswith("```"):
            json_text = json_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(json_text)
        print("✓ JSON parsed successfully.")
    except Exception as e:
        print(f"✗ Failed to parse JSON: {e}")
        print(f"Raw output preview: {raw_text[:300]}")
        continue
        
    # Check ai_rebuttal content
    rebuttal = parsed.get("ai_rebuttal", "")
    print(f"Rebuttal: {rebuttal}")
    
    # Verify links in rebuttal
    urls = re.findall(r'(https?://[^\s<>&"\')\]]+)', rebuttal)
    if not urls:
        print("✓ NO clickable URLs found in rebuttal text (as expected).")
    else:
        print(f"✗ Clickable URLs found in rebuttal text: {urls}")
        
    # Verify evidence source links in schema
    source_links = parsed.get("evidence_source_links", [])
    print(f"Evidence Source Links: {source_links}")
    valid_sources = []
    if source_links:
        valid_sources = [link for link in source_links if re.search(r'https?://', link)]
        if valid_sources:
            print(f"✓ Valid source links with URL: {valid_sources}")
            # Check if any link has a specific path (longer than just domain/newsroom main page)
            for link in valid_sources:
                parsed_url = re.search(r'https?://([^/]+)(/.*)?', link)
                if parsed_url:
                    path = (parsed_url.group(2) or "").strip("/")
                    if len(path) > 4:
                        print(f"✓ Specific URL path detected: {link}")
                    else:
                        print(f"⚠ Warning: Link might be generic/homepage: {link}")
        else:
            print("✗ Source links array exists but contains no URLs.")
    else:
        print("✗ evidence_source_links is empty.")
        
    # Verify fact-check results
    fact_check = parsed.get("fact_check", [])
    print(f"Fact Check: {fact_check}")
    fact_check_ok = True
    if case["has_evidence"]:
        if fact_check and len(fact_check) > 0:
            print(f"✓ Fact check generated: {len(fact_check)} items.")
            for item in fact_check:
                if not item.get("claim_text") or not item.get("verdict") or not item.get("explanation") or "source_url" not in item:
                    print(f"✗ Invalid fact check item (missing keys or empty): {item}")
                    fact_check_ok = False
                else:
                    print(f"  Item has source_url: {item.get('source_url')}")
            
            if case.get("expect_fake"):
                has_flagged_fake = False
                for item in fact_check:
                    verdict = str(item.get("verdict") or "").lower()
                    if verdict in ("inaccurate", "unverifiable"):
                        print(f"✓ Correctly flagged fake/made-up evidence as: {verdict}")
                        has_flagged_fake = True
                        break
                if not has_flagged_fake:
                    print("✗ Failed to flag fake/made-up evidence (expected inaccurate/unverifiable).")
                    fact_check_ok = False
        else:
            print("✗ Fact check is empty but case has evidence.")
            fact_check_ok = False
    else:
        if not fact_check:
            print("✓ Fact check is empty (as expected, no evidence).")
        else:
            # Sometime model returns a fact check even without explicit citations, check fields
            print(f"⚠ Fact check is not empty: {fact_check}")
            for item in fact_check:
                if not item.get("claim_text") or not item.get("verdict") or not item.get("explanation") or "source_url" not in item:
                    print(f"✗ Invalid fact check item: {item}")
                    fact_check_ok = False
        
    # Check for Chinese characters in the entire JSON payload
    def find_chinese_in_any(data):
        found = []
        if isinstance(data, str):
            found.extend(CHINESE_CHAR_RE.findall(data))
        elif isinstance(data, list):
            for item in data:
                found.extend(find_chinese_in_any(item))
        elif isinstance(data, dict):
            for k, v in data.items():
                # Don't check keys
                found.extend(find_chinese_in_any(v))
        return found

    chinese_chars = find_chinese_in_any(parsed)
    if chinese_chars:
        print(f"✗ Chinese characters detected: {set(chinese_chars)}")
    else:
        print("✓ No Chinese characters detected in any string field.")

    # Check for vague/general evidence phrases in AI rebuttal
    vague_phrases = ["nhiều nghiên cứu", "nhiều báo cáo", "các chuyên gia", "nhiều người", "studies show", "research shows"]
    found_vague = [p for p in vague_phrases if p in rebuttal.lower()]
    if found_vague:
        print(f"✗ Vague/general evidence phrases detected in rebuttal: {found_vague}")
    else:
        print("✓ No vague/general evidence phrases detected in rebuttal.")

    # Verify that the AI source links do not repeat the user's cited sources
    user_sources_dup = []
    if "apa" in case["user_argument"].lower() and any("apa" in link.lower() for link in source_links):
        user_sources_dup.append("APA")
    if "harvard" in case["user_argument"].lower() and any("harvard" in link.lower() for link in source_links):
        user_sources_dup.append("Harvard")
    if "irena" in case["user_argument"].lower() and any("irena" in link.lower() for link in source_links):
        user_sources_dup.append("IRENA")

    if user_sources_dup:
        print(f"✗ Duplicate user sources found in AI source links: {user_sources_dup}")
    else:
        print("✓ AI source links do not repeat user's cited sources.")
        
    # Check pass criteria: no CJK, no vague phrases, no duplicate user sources, no embedded URLs, and valid fact_check
    if not urls and not chinese_chars and not found_vague and not user_sources_dup and fact_check_ok:
        print("★ STATUS: PASS")
        success_count += 1
    else:
        print("☆ STATUS: FAIL (Embedded URLs, CJK chars, vague evidence, duplicate user sources, or invalid fact_check found)")

print("\n" + "=" * 80)
print(f"TESTING COMPLETE: {success_count}/{len(test_cases)} cases passed successfully!")
print("=" * 80)

if success_count == len(test_cases):
    sys.exit(0)
else:
    sys.exit(1)
