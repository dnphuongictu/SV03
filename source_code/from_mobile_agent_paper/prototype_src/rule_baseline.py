from __future__ import annotations

import re
import time
from typing import Any

from common import EVAL_PATH, RESULTS_DIR, load_jsonl, normalize_text, write_jsonl


PHONE_PATTERN = re.compile(r"\b0\d{8,10}\b")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}")
URI_PATTERN = re.compile(r"content://\S+")


def output(
    tool: str | None,
    arguments: dict[str, Any] | None = None,
    confirmation: bool = False,
    status: str | None = None,
) -> dict[str, Any]:
    result = {
        "tool": tool,
        "arguments": arguments or {},
        "requires_confirmation": confirmation,
    }
    if status:
        result["status"] = status
    return result


def parse_time(query: str) -> tuple[int, int] | None:
    """Parse Vietnamese time expressions like '6 giờ 30', 'bảy giờ', '2 giờ chiều'."""
    normalized = normalize_text(query)
    
    # Try numeric first: "6 giờ 30", "7 giờ"
    match = re.search(r"\b(\d{1,2})\s*(?:giờ|gio|h)\s*(\d{1,2})?\b", normalized)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
    else:
        # Try Vietnamese number words followed by "giờ/gio/h" to avoid
        # matching ordinals like "một cái" or pronouns in context
        word_to_num = {
            "khong": 0, "mot": 1, "hai": 2, "ba": 3, "bon": 4,
            "tu": 4, "nam": 5, "sau": 6, "bay": 7, "tam": 8,
            "chin": 9, "muoi": 10, "muoi mot": 11, "muoi hai": 12,
        }
        hour = -1
        minute = 0
        for word, num in sorted(word_to_num.items(), key=lambda x: -len(x[0])):
            pattern = rf"\b{re.escape(word)}\s+(?:giờ|gio|h)\b"
            if re.search(pattern, normalized):
                hour = num
                break
        if hour < 0:
            return None

    # Check original text WITH diacritics to avoid confusing pronoun "tôi"
    # (normalize → "toi") with evening marker "tối" (normalize → "toi")
    if re.search(r"\bchiều\b|\bbuổi chiều\b", query, flags=re.IGNORECASE) and 1 <= hour <= 11:
        hour += 12
    elif re.search(r"\btối\b|\bbuổi tối\b", query, flags=re.IGNORECASE) and 1 <= hour <= 11:
        hour += 12
    
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return None


def predict(query: str) -> dict[str, Any]:
    text = normalize_text(query)
    phones = PHONE_PATTERN.findall(query)
    emails = EMAIL_PATTERN.findall(query)
    uri_match = URI_PATTERN.search(query)

    # ============================================================
    # 1. UNSUPPORTED / CLARIFICATION (must be checked first)
    # ============================================================
    if any(term in text for term in ["pizza", "chuyen cho", "ngan hang"]):
        return output(None, status="unsupported")
    if text in {"mo no len", "lam di", "thuc hien no"}:
        return output(None, status="clarification")

    # ============================================================
    # 2. SETTINGS (check early to avoid conflicts with "mở" + noun)
    # ============================================================
    if "cai dat" in text or "setting" in text:
        setting = "general"
        if "wifi" in text or "wi-fi" in text:
            setting = "wifi"
        elif "bluetooth" in text:
            setting = "bluetooth"
        elif "may bay" in text or "airplane" in text:
            setting = "airplane_mode"
        elif "vi tri" in text or "location" in text:
            setting = "location"
        elif "man hinh" in text or "display" in text:
            setting = "display"
        elif "bao mat" in text or "security" in text:
            setting = "security"
        return output("open_settings", {"setting_type": setting})

    # ============================================================
    # 3. ALARM: show
    # ============================================================
    if "xem" in text and "bao thuc" in text:
        return output("ACTION_SHOW_ALARMS")

    # ============================================================
    # 4. ALARM: set
    # ============================================================
    if ("bao thuc" in text or "goi toi day" in text):
        # Check if missing time info (no digits AND no Vietnamese number words)
        has_number = bool(re.search(r"\d", query))
        has_word_number = bool(re.search(r"\b(một|mot|hai|ba|bốn|bon|năm|nam|sáu|sau|bảy|bay|tám|tam|chín|chin|mười|muoi)\b", text))
        if not has_number and not has_word_number:
            return output(None, status="clarification")
        parsed = parse_time(query)
        if not parsed:
            return output(None, status="clarification")
        hour, minute = parsed
        arguments: dict[str, Any] = {"EXTRA_HOUR": hour, "EXTRA_MINUTES": minute}
        label_match = re.search(r"(?:nhãn|nhan)\s+(.+)$", query, flags=re.IGNORECASE)
        if label_match:
            arguments["EXTRA_MESSAGE"] = label_match.group(1).strip()
        return output("ACTION_SET_ALARM", arguments)

    # ============================================================
    # 5. TIMER
    # ============================================================
    if "hen gio" in text:
        duration_match = re.search(
            r"(\d+)\s*(phút|phut|giờ|gio|giây|giay)", query, flags=re.IGNORECASE
        )
        if not duration_match:
            return output(None, status="clarification")
        units = {
            "phút": "minutes", "phut": "minutes",
            "giờ": "hours", "gio": "hours",
            "giây": "seconds", "giay": "seconds",
        }
        duration = f"{duration_match.group(1)} {units[duration_match.group(2).lower()]}"
        arguments = {"duration": duration}
        de_match = re.split(r"\bđể\b|\bde\b", query, maxsplit=1, flags=re.IGNORECASE)
        if len(de_match) > 1:
            arguments["EXTRA_MESSAGE"] = de_match[-1].strip()
        return output("ACTION_SET_TIMER", arguments)

    # ============================================================
    # 6. CALENDAR EVENT
    # ============================================================
    if "them lich" in text or "them su kien" in text:
        title = re.sub(r"^(Thêm lịch|Thêm sự kiện)\s+", "", query, flags=re.IGNORECASE)
        title = re.split(r"\blúc\b|\btại\b", title, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        arguments = {"TITLE": title, "DESCRIPTION": title}
        location_match = re.search(r"\btại\s+(.+)$", query, flags=re.IGNORECASE)
        if location_match:
            arguments["EVENT_LOCATION"] = location_match.group(1).strip()
        parsed = parse_time(query)
        if parsed:
            prefix = "tomorrow " if "mai" in text else ""
            arguments["EXTRA_EVENT_BEGIN_TIME"] = f"{prefix}{parsed[0]:02d}:{parsed[1]:02d}"
        return output("ACTION_INSERT_EVENT", arguments, True)

    # ============================================================
    # 7. CONTACT: insert
    # ============================================================
    if "them lien he" in text:
        if not phones:
            return output(None, status="clarification")
        name = re.sub(r"^.*?thêm liên hệ\s+", "", query, flags=re.IGNORECASE)
        name = re.split(r"\bsố\b", name, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        return output(
            "ACTION_INSERT_CONTACT",
            {"contact_info": {"name": name, "phone": phones[0]}},
            True,
        )

    # ============================================================
    # 8. CONTACT: lookup (check BEFORE generic "tìm" for map)
    # ============================================================
    if "tim so dien thoai" in text or "tim email" in text or "tim thong tin" in text:
        name = re.sub(r"^.*?\bcủa\b|\btrong danh bạ.*$", "", query, flags=re.IGNORECASE).strip()
        name = re.sub(r"^(anh|chị|chi|bạn|ban)\s+", "", name, flags=re.IGNORECASE)
        key = "email" if "email" in text else "phone"
        return output("get_contact_info", {"name": name, "key": key})

    # ============================================================
    # 9. CONTACT: view by URI
    # ============================================================
    if "thong tin lien he" in text and uri_match:
        return output("ACTION_VIEW_CONTACT", {"contact_uri": uri_match.group(0)})

    # ============================================================
    # 10. CONTACT: pick
    # ============================================================
    if "chon mot" in text and ("email" in text or "dia chi" in text or "so dien thoai" in text):
        data_type = "EMAIL" if "email" in text else ("PHONE" if "so dien thoai" in text else "ADDRESS")
        return output("ACTION_PICK", {"data_type": data_type})

    # ============================================================
    # 11. DIAL
    # ============================================================
    if text.startswith("goi"):
        if not phones:
            return output(None, status="clarification")
        return output("dial", {"phone_number": phones[0]}, True)

    # ============================================================
    # 12. SMS
    # ============================================================
    if text.startswith("nhan") or "soan tin" in text:
        if not phones:
            return output(None, status="clarification")
        subject = ""
        subject_match = re.search(r"tiêu đề\s+([^,]+)", query, flags=re.IGNORECASE)
        if subject_match:
            subject = subject_match.group(1).strip()
        body = ""
        body_match = re.search(r"(?:rằng|rang|noi dung|nội dung)\s+(.+)$", query, flags=re.IGNORECASE)
        if body_match:
            body = body_match.group(1).strip()
        return output(
            "send_message",
            {"phone_number": phones[0], "subject": subject, "body": body},
            True,
        )

    # ============================================================
    # 13. EMAIL
    # ============================================================
    if "email" in text or "soan thu" in text:
        if not emails:
            return output(None, status="clarification")
        subject_match = re.search(r"(?:tiêu đề|chủ đề)\s+([^,]+)", query, flags=re.IGNORECASE)
        body_match = re.search(r"nội dung\s+(.+)$", query, flags=re.IGNORECASE)
        if not subject_match or not body_match:
            return output(None, status="clarification")
        return output(
            "send_email",
            {
                "to": emails,
                "subject": subject_match.group(1).strip(),
                "body": body_match.group(1).strip(),
            },
            True,
        )

    # ============================================================
    # 14. WEB SEARCH (check BEFORE generic "tìm" for map)
    # ============================================================
    if "tim tren google" in text or "tim kiem" in text:
        query_text = re.sub(r"^.*?Google\s+|^.*?tìm kiếm\s+", "", query, flags=re.IGNORECASE)
        return output("web_search", {"query": query_text.strip(), "engine": "google"})

    # ============================================================
    # 15. MAP (specific patterns before generic "tìm")
    # ============================================================
    if "chi duong" in text or "chi duong toi" in text:
        query_text = re.sub(r"^(Chỉ đường tới|chi duong toi)\s+", "", query, flags=re.IGNORECASE)
        if query_text.strip():
            return output("search_location", {"query": query_text.strip()})

    if "ban do" in text:
        query_text = re.sub(r"^(Tìm|Tim)\s+", "", query, flags=re.IGNORECASE)
        query_text = re.sub(r"\s+trên bản đồ$|\s+trên ban do$", "", query_text, flags=re.IGNORECASE)
        if query_text.strip():
            return output("search_location", {"query": query_text.strip()})

    # ============================================================
    # 16. CAMERA: open still mode (check before capture)
    # ============================================================
    if "mo may anh" in text or "chup hinh" in text:
        return output("INTENT_ACTION_STILL_IMAGE_CAMERA")

    # ============================================================
    # 17. CAMERA: capture photo
    # ============================================================
    if "chup mot buc anh" in text:
        return output("ACTION_IMAGE_CAPTURE")

    # ============================================================
    # 18. CAMERA: open video mode (check before capture)
    # ============================================================
    if "che do quay phim" in text or "mo che do quay" in text:
        return output("INTENT_ACTION_VIDEO_CAMERA")

    # ============================================================
    # 19. CAMERA: capture video
    # ============================================================
    if "quay mot video" in text or "quay video" in text:
        return output("ACTION_VIDEO_CAPTURE")

    # ============================================================
    # 20. SETTINGS (general - catch-all)
    # ============================================================
    if "cai dat" in text or "setting" in text:
        setting = "general"
        if "vi tri" in text or "location" in text:
            setting = "location"
        elif "man hinh" in text or "display" in text:
            setting = "display"
        elif "bao mat" in text or "security" in text:
            setting = "security"
        return output("open_settings", {"setting_type": setting})

    # ============================================================
    # 21. FILE: pick image
    # ============================================================
    if "chon mot anh" in text or "chon anh" in text:
        return output("ACTION_GET_CONTENT", {"mime_type": "image/*", "allow_multiple": False})

    # ============================================================
    # 22. FILE: open documents
    # ============================================================
    if "mo nhieu tep pdf" in text or "mo tep pdf" in text:
        return output("ACTION_OPEN_DOCUMENT", {"mime_types": ["application/pdf"], "allow_multiple": True})

    # ============================================================
    # 23. FILE: create document
    # ============================================================
    if "tao tep van ban" in text or "tao tep" in text:
        filename_match = re.search(r"tên\s+(\S+)", query, flags=re.IGNORECASE)
        if not filename_match:
            return output(None, status="clarification")
        return output(
            "ACTION_CREATE_DOCUMENT",
            {"mime_type": "text/plain", "initial_name": filename_match.group(1)},
        )

    # ============================================================
    # 24. FALLBACK: unsupported
    # ============================================================
    return output(None, status="unsupported")


def main() -> None:
    examples = load_jsonl(EVAL_PATH)
    predictions = []
    for example in examples:
        start = time.perf_counter()
        prediction = predict(example["query"])
        elapsed_ms = (time.perf_counter() - start) * 1000
        predictions.append(
            {
                "id": example["id"],
                "prediction": prediction,
                "latency_ms": round(elapsed_ms, 4),
            }
        )
    output_path = RESULTS_DIR / "rule_baseline_predictions.jsonl"
    write_jsonl(output_path, predictions)
    print(f"Wrote {len(predictions)} predictions to {output_path}")


if __name__ == "__main__":
    main()
