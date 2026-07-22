"""Generate code-switching (Vietnamese-English mixed) queries for robustness testing.

Creates ~100 code-switched queries from templates, testing the model's ability
to handle common Việt-Anh patterns in mobile commands.

Output: prototype/data/eval/codeswitch_queries.jsonl

Usage:
    python -X utf8 src/generate_codeswitch_queries.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"
EVAL_PATH = ROOT / "data" / "eval" / "vi_droidcall_v1.jsonl"
OUT_PATH = ROOT / "data" / "eval" / "codeswitch_queries.jsonl"

# ── CS patterns: (id_suffix, query_template, expected_tool) ─────────────────
# Each row: (id_suffix, query_template, expected_tool)
# expected_tool MUST match a tool name in android_tools.json exactly.
CS_TEMPLATES: list[tuple[str, str, str]] = [
    # ── Call/Dial ──
    ("call_01", "Gọi cho anh Minh {by} phone number 0912345678", "dial"),
    ("call_02", "Gọi {to} 0987654321 now", "dial"),
    ("call_03", "Please gọi số này 0912345678", "dial"),
    ("call_04", "Call {for} me số 0909123456", "dial"),
    ("call_05", "Dial số 0987654321 giúp tôi", "dial"),

    # ── Alarm/Timer ──
    ("alarm_01", "Set alarm {for} 6 giờ sáng với label đi học", "ACTION_SET_ALARM"),
    ("alarm_02", "Đặt báo thức {at} 7:30 AM nhãn tập gym", "ACTION_SET_ALARM"),
    ("alarm_03", "Set timer {for} 15 minutes để luộc trứng", "ACTION_SET_TIMER"),
    ("alarm_04", "Hẹn giờ 10 minutes nghỉ giải lao", "ACTION_SET_TIMER"),
    ("alarm_05", "Wake me up {at} 5 giờ sáng ngày mai", "ACTION_SET_ALARM"),

    # ── Settings ──
    ("settings_01", "Open {the} settings Wi-Fi", "open_settings"),
    ("settings_02", "Mở cài đặt Bluetooth and turn on location", "open_settings"),
    ("settings_03", "Open cài đặt display và set brightness", "open_settings"),
    ("settings_04", "Mở phần security settings please", "open_settings"),
    ("settings_05", "Turn {on} Wi-Fi và mở cài đặt", "open_settings"),

    # ── Message ──
    ("sms_01", "Send message {to} 0912345678 nội dung tôi đến muộn 10 phút", "send_message"),
    ("sms_02", "Nhắn 0987654321 với nội dung I'll be late", "send_message"),
    ("sms_03", "Send an SMS {to} 0909123456 says cảm ơn bạn", "send_message"),

    # ── Email ──
    ("sms_04", "Send email {to} minh@gmail.com với subject Báo cáo", "send_email"),
    ("sms_05", "Gửi email tới lan@example.com with subject Họp nhóm", "send_email"),
    ("sms_06", "Send email {to} a@example.com and b@example.com cc c@example.com", "send_email"),
    ("sms_07", "Soạn email {for} hung@company.vn body gửi báo cáo tuần này", "send_email"),

    # ── Web Search ──
    ("web_01", "Search {on} Google cách cài Python on Windows", "web_search"),
    ("web_02", "Tìm {on} Google thời tiết Hà Nội today", "web_search"),
    ("web_03", "Google {for} nhà hàng ngon near me", "web_search"),
    ("web_04", "Search {for} hướng dẫn nấu bún bò Huế online", "web_search"),

    # ── Map / Location ──
    ("map_01", "Find đường {to} sân bay Đà Nẵng on map", "search_location"),
    ("map_02", "Chỉ đường {to} bệnh viện Bạch Mai using Google Maps", "search_location"),
    ("map_03", "Search {for} khách sạn gần đây on bản đồ", "search_location"),
    ("map_04", "Navigate {to} Hồ Gươm please", "search_location"),

    # ── Camera ──
    ("camera_01", "Open {the} camera để tôi chụp hình", "INTENT_ACTION_STILL_IMAGE_CAMERA"),
    ("camera_02", "Take a photo ngay bây giờ", "ACTION_IMAGE_CAPTURE"),
    ("camera_03", "Start video recording mode please", "INTENT_ACTION_VIDEO_CAMERA"),
    ("camera_04", "Quay {a} video và save it", "ACTION_VIDEO_CAPTURE"),

    # ── File ──
    ("file_01", "Pick {a} photo từ máy", "ACTION_PICK"),
    ("file_02", "Open {a} PDF file để xem lâu dài", "ACTION_OPEN_DOCUMENT"),
    ("file_03", "Tạo file mới tên report.txt please", "ACTION_CREATE_DOCUMENT"),
    ("file_04", "Select multiple image files và choose", "ACTION_GET_CONTENT"),

    # ── Contact ──
    ("contact_01", "Tìm phone number của anh Minh in contacts", "get_contact_info"),
    ("contact_02", "Look {for} anh Hùng's email trong danh bạ", "get_contact_info"),
    ("contact_03", "Add {a} new contact tên Lan Anh số 0912345678", "ACTION_INSERT_CONTACT"),

    # ── Event ──
    ("event_01", "Add {a} calendar event họp nhóm {at} 2 PM tomorrow", "ACTION_INSERT_EVENT"),
    ("event_02", "Thêm lịch họp {at} 9 AM sáng mai với title họp team", "ACTION_INSERT_EVENT"),

    # ── Mixed long queries ──
    ("long_01", "Please set {an} alarm {for} 6:30 AM tomorrow with label đi học và also send {a} reminder", "ACTION_SET_ALARM"),
    ("long_02", "Mở Wi-Fi settings and then open Bluetooth too", "open_settings"),
    ("long_03", "Search {for} phở bò gần đây on Google Maps and show {the} directions", "search_location"),
    ("long_04", "Send {a} text {to} 0912345678 nội dung họp {at} 3 PM và also email {to} minh@gmail.com", "send_message"),
]

# Prepositions to insert
PREPOSITIONS = ["by", "to", "for", "at", "on", "in", "of", "with", "the", "a", "an"]


def fill_template(template: str) -> str:
    """Replace {word} placeholders either with the word or skip."""
    import re

    def replacer(match):
        word = match.group(1)
        return word  # Always insert the English word

    result = re.sub(r'\{(\w+)\}', replacer, template)
    return result


def main() -> None:
    # Load tools to validate expected tool names
    tools = json.loads(TOOLS_PATH.read_text("utf-8"))
    tool_names = {t["name"] for t in tools}

    output_rows: list[dict[str, Any]] = []
    for idx, (suffix, template, expected_tool) in enumerate(CS_TEMPLATES):
        query = fill_template(template)
        sample_id = f"cs_{suffix}"

        # Validate expected_tool exists
        if expected_tool not in tool_names:
            print(f"WARNING: expected_tool '{expected_tool}' not found in tools! "
                  f"(sample {sample_id})")

        expected_args: dict = {}

        output_rows.append({
            "id": sample_id,
            "query": query,
            "template": template,
            "expected": {
                "tool": expected_tool,
                "arguments": expected_args,
                "requires_confirmation": True,  # conservative
            },
        })

    # Write output
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in output_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output_rows)} code-switching queries to {OUT_PATH}")
    print("\n--- Examples ---")
    for r in output_rows[:5]:
        print(f"  [{r['id']}] {r['expected']['tool']:40s} | {r['query']}")
    print(f"\nTool distribution:")
    from collections import Counter
    tool_counts = Counter(r["expected"]["tool"] for r in output_rows)
    for t, n in sorted(tool_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:40s}: {n}")


if __name__ == "__main__":
    main()