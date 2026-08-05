"""Create the fresh locked ICTA evaluation split and its audit artifacts.

This script is intentionally deterministic. It writes:
  - data/eval/vi_droidcall_fresh_test_locked_20260626.jsonl
  - data/eval/vi_droidcall_fresh_test_locked_20260626_ledger.csv
  - results/fresh_test_locked_20260626/leakage_report.json
  - results/fresh_test_locked_20260626/final_config.json

The split is locked before model selection/evaluation on this data. Do not use
it for tuning alpha, K, prompts, augmentation, thresholds, or choosing versions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from common import ROOT, load_json, load_jsonl, write_jsonl
from validate import ToolValidator


LOCK_DATE = "20260626"
EVAL_DIR = ROOT / "data" / "eval"
RESULT_DIR = ROOT / "results" / f"fresh_test_locked_{LOCK_DATE}"
TEST_PATH = EVAL_DIR / f"vi_droidcall_fresh_test_locked_{LOCK_DATE}.jsonl"
LEDGER_PATH = EVAL_DIR / f"vi_droidcall_fresh_test_locked_{LOCK_DATE}_ledger.csv"
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"


def expected(tool: str, arguments: dict[str, Any], tools: dict[str, dict]) -> dict[str, Any]:
    return {
        "tool": tool,
        "arguments": arguments,
        "requires_confirmation": bool(tools[tool]["confirmation"]),
    }


def null_expected(status: str) -> dict[str, Any]:
    return {"tool": None, "arguments": {}, "requires_confirmation": False, "status": status}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalize(text: Any) -> str:
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(
        ch
        for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9@.+:/_* -]+", " ", text.lower()).strip()


def char_ngrams(text: str, n: int = 3) -> set[str]:
    text = re.sub(r"\s+", " ", normalize(text))
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def jaccard(a: str, b: str) -> float:
    aa, bb = char_ngrams(a), char_ngrams(b)
    if not aa and not bb:
        return 1.0
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def build_cases(tools: dict[str, dict]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(tool: str, query: str, args: dict[str, Any], group: str, phenomena: str) -> None:
        rows.append(
            {
                "query": query,
                "expected": expected(tool, args, tools),
                "group": group,
                "source": "manual_codex_locked_20260626",
                "phenomena": phenomena,
            }
        )

    def neg(query: str, status: str, phenomena: str) -> None:
        rows.append(
            {
                "query": query,
                "expected": null_expected(status),
                "group": "negative_clarification",
                "source": "manual_codex_locked_20260626",
                "phenomena": phenomena,
            }
        )

    add("ACTION_CREATE_DOCUMENT", "Tạo file markdown tên ghi_chu_hop.md để tôi chọn nơi lưu", {"mime_type": "text/markdown", "initial_name": "ghi_chu_hop.md"}, "files_settings", "file_creation")
    add("ACTION_CREATE_DOCUMENT", "Lưu một bảng tính mới tên ngan_sach_gia_dinh.xlsx", {"mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "initial_name": "ngan_sach_gia_dinh.xlsx"}, "files_settings", "file_creation")
    add("ACTION_CREATE_DOCUMENT", "Tạo tài liệu JSON rỗng tên config_backup.json", {"mime_type": "application/json", "initial_name": "config_backup.json"}, "files_settings", "file_creation")
    add("ACTION_CREATE_DOCUMENT", "Cho tôi tạo file PDF mới tên phieu_thu_07.pdf", {"mime_type": "application/pdf", "initial_name": "phieu_thu_07.pdf"}, "files_settings", "file_creation")

    add("ACTION_EDIT_CONTACT", "Mở màn hình sửa liên hệ content://contacts/people/701", {"contact_uri": "content://contacts/people/701"}, "contacts", "uri")
    add("ACTION_EDIT_CONTACT", "Cập nhật contact URI contacts://team/linh-09 với email mới", {"contact_uri": "contacts://team/linh-09", "contact_info": {"email": "linh09@work.vn"}}, "contacts", "uri_optional_object")
    add("ACTION_EDIT_CONTACT", "Sửa thông tin danh bạ ở content://com.android.contacts/contacts/214", {"contact_uri": "content://com.android.contacts/contacts/214"}, "contacts", "uri")
    add("ACTION_EDIT_CONTACT", "Tôi muốn chỉnh contact contacts://family/me-hoa", {"contact_uri": "contacts://family/me-hoa"}, "contacts", "honorific")

    add("ACTION_GET_CONTENT", "Chọn một ảnh để tôi gửi lên biểu mẫu", {"mime_type": "image/*"}, "files_settings", "temporary_file_access")
    add("ACTION_GET_CONTENT", "Lấy nhiều file PDF từ bộ nhớ để đính kèm", {"mime_type": "application/pdf", "allow_multiple": True}, "files_settings", "multiple_files")
    add("ACTION_GET_CONTENT", "Mở bộ chọn âm thanh, tôi cần một file wav", {"mime_type": "audio/wav"}, "files_settings", "mime_specific")
    add("ACTION_GET_CONTENT", "Chọn video bất kỳ cho phần upload", {"mime_type": "video/*"}, "files_settings", "temporary_file_access")

    add("ACTION_GET_RINGTONE", "Vào màn hình chọn âm báo cuộc gọi", {}, "files_settings", "zero_arg")
    add("ACTION_GET_RINGTONE", "Cho tôi đổi ringtone mặc định", {}, "files_settings", "english_mix")
    add("ACTION_GET_RINGTONE", "Vào danh sách âm báo để chọn chuông mới", {}, "files_settings", "paraphrase")
    add("ACTION_GET_RINGTONE", "Tôi cần chọn một âm thanh làm chuông điện thoại", {}, "files_settings", "paraphrase")

    add("ACTION_IMAGE_CAPTURE", "Chụp ngay một ảnh biên nhận và trả về file", {}, "camera_media", "capture_now")
    add("ACTION_IMAGE_CAPTURE", "Bấm chụp hình tức thì giúp tôi", {}, "camera_media", "colloquial")
    add("ACTION_IMAGE_CAPTURE", "Capture một tấm ảnh rồi lưu URI lại", {}, "camera_media", "english_mix")
    add("ACTION_IMAGE_CAPTURE", "Chụp ảnh sản phẩm này ngay bây giờ", {}, "camera_media", "capture_now")

    add("ACTION_INSERT_CONTACT", "Thêm liên hệ mới tên Bùi Gia Hân số 0855123456", {"contact_info": {"name": "Bùi Gia Hân", "phone": "0855123456"}}, "contacts", "new_contact")
    add("ACTION_INSERT_CONTACT", "Lưu danh bạ cho Trương Minh Nhật, email nhat.truong@example.vn", {"contact_info": {"name": "Trương Minh Nhật", "email": "nhat.truong@example.vn"}}, "contacts", "new_contact")
    add("ACTION_INSERT_CONTACT", "Tạo contact công ty: Lan Anh Logistics, điện thoại 02877770000", {"contact_info": {"name": "Lan Anh Logistics", "phone": "02877770000"}}, "contacts", "organization")
    add("ACTION_INSERT_CONTACT", "Thêm Nguyễn Phúc Khang vào danh bạ, công ty Delta Lab, địa chỉ 9 Nguyễn Huệ", {"contact_info": {"name": "Nguyễn Phúc Khang", "company": "Delta Lab", "address": "9 Nguyễn Huệ"}}, "contacts", "multi_field")

    add("ACTION_INSERT_EVENT", "Thêm lịch demo sản phẩm thứ Năm 14:15 tại phòng C4", {"TITLE": "demo sản phẩm", "DESCRIPTION": "demo sản phẩm", "EVENT_LOCATION": "phòng C4", "EXTRA_EVENT_BEGIN_TIME": "Thursday 14:15"}, "alarm_calendar", "calendar_event")
    add("ACTION_INSERT_EVENT", "Tạo sự kiện khám tổng quát ngày 2026-07-03 lúc 08:00", {"TITLE": "khám tổng quát", "DESCRIPTION": "khám tổng quát", "EXTRA_EVENT_BEGIN_TIME": "2026-07-03 08:00"}, "alarm_calendar", "date_time")
    add("ACTION_INSERT_EVENT", "Đặt lịch gọi phụ huynh tối mai 19h30", {"TITLE": "gọi phụ huynh", "DESCRIPTION": "gọi phụ huynh", "EXTRA_EVENT_BEGIN_TIME": "tomorrow 19:30"}, "alarm_calendar", "relative_time")
    add("ACTION_INSERT_EVENT", "Ghi vào lịch: workshop AI, cả ngày 12 tháng 9", {"TITLE": "workshop AI", "DESCRIPTION": "workshop AI", "EXTRA_EVENT_BEGIN_TIME": "2026-09-12", "EXTRA_EVENT_ALL_DAY": True}, "alarm_calendar", "all_day")

    add("ACTION_OPEN_DOCUMENT", "Mở một file csv đã lưu trong máy", {"mime_types": ["text/csv"]}, "files_settings", "persistent_file_access")
    add("ACTION_OPEN_DOCUMENT", "Chọn nhiều tài liệu Word để xem", {"mime_types": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"], "allow_multiple": True}, "files_settings", "multiple_files")
    add("ACTION_OPEN_DOCUMENT", "Tôi muốn mở ảnh định dạng webp", {"mime_types": ["image/webp"]}, "files_settings", "mime_specific")
    add("ACTION_OPEN_DOCUMENT", "Mở tài liệu zip từ bộ nhớ lâu dài", {"mime_types": ["application/zip"]}, "files_settings", "persistent_file_access")

    add("ACTION_PICK", "Mở danh bạ cho tôi chọn email", {"data_type": "EMAIL"}, "contacts", "picker")
    add("ACTION_PICK", "Cho tôi chọn số điện thoại từ contact", {"data_type": "PHONE"}, "contacts", "picker")
    add("ACTION_PICK", "Mở bộ chọn địa chỉ trong danh bạ", {"data_type": "ADDRESS"}, "contacts", "picker")
    add("ACTION_PICK", "Tôi cần chọn một liên hệ bất kỳ", {"data_type": "ALL"}, "contacts", "picker")

    add("ACTION_SET_ALARM", "Cài chuông 4 giờ 50 sáng nhắc ra sân bay", {"EXTRA_HOUR": 4, "EXTRA_MINUTES": 50, "EXTRA_MESSAGE": "ra sân bay"}, "alarm_calendar", "early_time")
    add("ACTION_SET_ALARM", "Đặt báo thức lúc 13:05 cho ca học chiều", {"EXTRA_HOUR": 13, "EXTRA_MINUTES": 5, "EXTRA_MESSAGE": "ca học chiều"}, "alarm_calendar", "colon_time")
    add("ACTION_SET_ALARM", "Alarm 21h10 mỗi thứ Ba và thứ Sáu", {"EXTRA_HOUR": 21, "EXTRA_MINUTES": 10, "EXTRA_DAYS": ["Tuesday", "Friday"]}, "alarm_calendar", "repeat_days")
    add("ACTION_SET_ALARM", "Báo tôi lúc 0 giờ 15 để kiểm tra server", {"EXTRA_HOUR": 0, "EXTRA_MINUTES": 15, "EXTRA_MESSAGE": "kiểm tra server"}, "alarm_calendar", "midnight")

    add("ACTION_SET_TIMER", "Hẹn bộ đếm 7 phút cho trà", {"duration": "7 minutes", "EXTRA_MESSAGE": "trà"}, "alarm_calendar", "timer")
    add("ACTION_SET_TIMER", "Đếm ngược 90 giây", {"duration": "90 seconds"}, "alarm_calendar", "short_duration")
    add("ACTION_SET_TIMER", "Timer 3 giờ 20 phút cho máy giặt", {"duration": "3 hours 20 minutes", "EXTRA_MESSAGE": "máy giặt"}, "alarm_calendar", "long_duration")
    add("ACTION_SET_TIMER", "Đặt đồng hồ bấm ngược nửa tiếng", {"duration": "30 minutes"}, "alarm_calendar", "colloquial_duration")

    add("ACTION_SHOW_ALARMS", "Xem các chuông báo đã tạo", {}, "alarm_calendar", "zero_arg")
    add("ACTION_SHOW_ALARMS", "Liệt kê alarm hiện tại trong máy", {}, "alarm_calendar", "english_mix")
    add("ACTION_SHOW_ALARMS", "Mở trang quản lý báo thức", {}, "alarm_calendar", "paraphrase")
    add("ACTION_SHOW_ALARMS", "Có báo thức nào đang bật không, mở ra xem", {}, "alarm_calendar", "question_form")

    add("ACTION_VIDEO_CAPTURE", "Quay ngay clip hiện trường và lưu kết quả", {}, "camera_media", "capture_now")
    add("ACTION_VIDEO_CAPTURE", "Record video tức thì giúp tôi", {}, "camera_media", "english_mix")
    add("ACTION_VIDEO_CAPTURE", "Bấm quay một đoạn video bây giờ", {}, "camera_media", "capture_now")
    add("ACTION_VIDEO_CAPTURE", "Ghi hình nhanh rồi trả về file video", {}, "camera_media", "capture_now")

    add("ACTION_VIEW_CONTACT", "Hiển thị hồ sơ content://contacts/people/802", {"contact_uri": "content://contacts/people/802"}, "contacts", "uri")
    add("ACTION_VIEW_CONTACT", "Xem chi tiết liên hệ contacts://office/accountant", {"contact_uri": "contacts://office/accountant"}, "contacts", "uri")
    add("ACTION_VIEW_CONTACT", "Mở profile contact content://com.android.contacts/contacts/512", {"contact_uri": "content://com.android.contacts/contacts/512"}, "contacts", "english_mix")
    add("ACTION_VIEW_CONTACT", "Cho tôi xem liên hệ contacts://club/leader", {"contact_uri": "contacts://club/leader"}, "contacts", "uri")

    add("INTENT_ACTION_STILL_IMAGE_CAMERA", "Mở camera chụp ảnh, tôi tự bấm sau", {}, "camera_media", "open_only")
    add("INTENT_ACTION_STILL_IMAGE_CAMERA", "Bật ứng dụng máy ảnh ở chế độ photo", {}, "camera_media", "english_mix")
    add("INTENT_ACTION_STILL_IMAGE_CAMERA", "Vào camera để chuẩn bị chụp", {}, "camera_media", "open_only")
    add("INTENT_ACTION_STILL_IMAGE_CAMERA", "Khởi động máy ảnh nhưng đừng chụp ngay", {}, "camera_media", "open_only")

    add("INTENT_ACTION_VIDEO_CAMERA", "Chuẩn bị giao diện video trong camera", {}, "camera_media", "open_only")
    add("INTENT_ACTION_VIDEO_CAMERA", "Bật video camera để tôi tự record", {}, "camera_media", "english_mix")
    add("INTENT_ACTION_VIDEO_CAMERA", "Vào chế độ quay video trong app camera", {}, "camera_media", "open_only")
    add("INTENT_ACTION_VIDEO_CAMERA", "Chuẩn bị màn hình quay phim, chưa cần quay", {}, "camera_media", "open_only")

    add("dial", "Quay số 090 455 6677 cho nhà xe", {"phone_number": "0904556677"}, "message_call", "phone")
    add("dial", "Gọi tổng đài 1900 9095", {"phone_number": "19009095"}, "message_call", "hotline")
    add("dial", "Mở dialer với số +84 912 000 333", {"phone_number": "+84912000333"}, "message_call", "international_format")
    add("dial", "Bấm số 028 7300 6688 nhưng để tôi xác nhận", {"phone_number": "02873006688"}, "message_call", "confirmation_sensitive")

    add("get_contact_info", "Lấy email của cô Mai Phương", {"name": "Mai Phương", "key": "email"}, "contacts", "honorific")
    add("get_contact_info", "Số điện thoại bạn Quốc Huy là gì", {"name": "Quốc Huy", "key": "phone"}, "contacts", "honorific")
    add("get_contact_info", "Tra địa chỉ của bác Tám trong danh bạ", {"name": "Tám", "key": "address"}, "contacts", "honorific")
    add("get_contact_info", "Cho tôi URI liên hệ của Trần Khánh Vy", {"name": "Trần Khánh Vy", "key": "uri"}, "contacts", "uri_lookup")

    add("get_contact_info_from_uri", "Từ contacts://supplier/77 lấy email", {"contact_uri": "contacts://supplier/77", "key": "email"}, "contacts", "uri_lookup")
    add("get_contact_info_from_uri", "Tra phone từ content://contacts/people/909", {"contact_uri": "content://contacts/people/909", "key": "phone"}, "contacts", "english_mix")
    add("get_contact_info_from_uri", "Lấy địa chỉ trong URI contacts://family/ba", {"contact_uri": "contacts://family/ba", "key": "address"}, "contacts", "uri_lookup")
    add("get_contact_info_from_uri", "content://com.android.contacts/contacts/18 có email nào", {"contact_uri": "content://com.android.contacts/contacts/18", "key": "email"}, "contacts", "question_form")

    add("open_settings", "Mở phần cài đặt bàn phím", {"setting_type": "input_method"}, "files_settings", "setting")
    add("open_settings", "Vào mục ngày giờ của hệ thống", {"setting_type": "date"}, "files_settings", "setting")
    add("open_settings", "Bật trang cấu hình APN", {"setting_type": "apn"}, "files_settings", "setting")
    add("open_settings", "Mở cài đặt thẻ nhớ", {"setting_type": "memory_card"}, "files_settings", "setting")

    add("search_location", "Tìm đường đến Bảo tàng Mỹ thuật Đà Nẵng", {"query": "Bảo tàng Mỹ thuật Đà Nẵng"}, "map_web", "location")
    add("search_location", "Mở bản đồ tìm 42 Trần Phú, Nha Trang", {"query": "42 Trần Phú, Nha Trang"}, "map_web", "address")
    add("search_location", "Định vị quán bún cá Hạnh Nhiên gần đây", {"query": "quán bún cá Hạnh Nhiên gần đây"}, "map_web", "nearby")
    add("search_location", "Chỉ đường tới Ga Biên Hòa", {"query": "Ga Biên Hòa"}, "map_web", "directions")

    add("send_email", "Soạn email tới hr@vietlab.vn, tiêu đề Lịch phỏng vấn, nội dung Tôi xác nhận tham gia lúc 9h", {"to": ["hr@vietlab.vn"], "subject": "Lịch phỏng vấn", "body": "Tôi xác nhận tham gia lúc 9h"}, "message_call", "email")
    add("send_email", "Gửi mail cho an.ngo@school.edu và khoa@school.edu subject Cập nhật đề cương body Em gửi bản mới", {"to": ["an.ngo@school.edu", "khoa@school.edu"], "subject": "Cập nhật đề cương", "body": "Em gửi bản mới"}, "message_call", "multi_recipient")
    add("send_email", "Email đến finance@delta.vn với chủ đề Hóa đơn tháng 6, nội dung: Nhờ kiểm tra giúp tôi", {"to": ["finance@delta.vn"], "subject": "Hóa đơn tháng 6", "body": "Nhờ kiểm tra giúp tôi"}, "message_call", "email")
    add("send_email", "Compose mail to qa-team@example.com subject Regression log body Build 17 đã pass smoke", {"to": ["qa-team@example.com"], "subject": "Regression log", "body": "Build 17 đã pass smoke"}, "message_call", "english_mix")

    add("send_message", "Nhắn 0866 120 120: em gửi xe ở cổng số 2", {"phone_number": "0866120120", "body": "em gửi xe ở cổng số 2"}, "message_call", "sms")
    add("send_message", "Soạn SMS tới +84 934 555 121 nội dung Đơn hàng đã giao", {"phone_number": "+84934555121", "body": "Đơn hàng đã giao"}, "message_call", "international_format")
    add("send_message", "Gửi tin cho 0914 222 888 rằng tối nay đổi sang 8h", {"phone_number": "0914222888", "body": "tối nay đổi sang 8h"}, "message_call", "sms")
    add("send_message", "Text 0987000111: meeting moved to room 305", {"phone_number": "0987000111", "body": "meeting moved to room 305"}, "message_call", "english_mix")

    add("web_search", "Tìm trên Google cách kiểm tra pin chai Android", {"query": "cách kiểm tra pin chai Android", "engine": "google"}, "map_web", "web")
    add("web_search", "Search giá vé tàu Sài Gòn Quy Nhơn tháng 8", {"query": "giá vé tàu Sài Gòn Quy Nhơn tháng 8"}, "map_web", "english_mix")
    add("web_search", "Tra cứu bài hướng dẫn nộp thuế cá nhân online", {"query": "hướng dẫn nộp thuế cá nhân online"}, "map_web", "web")
    add("web_search", "Tìm bằng baidu cụm từ học tiếng Trung HSK 3", {"query": "học tiếng Trung HSK 3", "engine": "baidu"}, "map_web", "engine_variant")

    for query, status, phenomena in [
        ("Gọi giúp tôi", "clarification", "missing_phone_or_contact"),
        ("Nhắn cho người đó là tôi tới rồi", "clarification", "missing_recipient"),
        ("Gửi email báo cáo đi", "clarification", "missing_recipient_subject_body"),
        ("Mai nhớ đánh thức tôi nhưng tôi chưa nói mấy giờ", "clarification", "missing_time"),
        ("Tạo sự kiện họp", "clarification", "missing_time"),
        ("Mở tài liệu", "clarification", "missing_mime_type"),
        ("Tôi muốn lấy tài liệu nhưng chưa nói loại nào", "clarification", "missing_mime_type"),
        ("Đi tới đâu đó nhưng tôi chưa nói địa điểm", "clarification", "missing_location"),
        ("Tra số trong danh bạ", "clarification", "missing_contact"),
        ("Sửa liên hệ của mẹ", "clarification", "missing_contact_uri"),
        ("Xem liên hệ", "clarification", "missing_contact_uri"),
        ("Tạo file mới", "clarification", "missing_file_type_or_name"),
        ("Nhắc tôi việc quan trọng", "clarification", "missing_time_or_action"),
        ("Tìm kiếm trên web", "clarification", "missing_query"),
        ("Mở cài đặt mạng nào đó", "clarification", "ambiguous_setting"),
        ("Bật playlist nhạc acoustic trong máy", "unsupported", "unsupported_media_playback"),
        ("Xóa toàn bộ ảnh trong thư viện", "unsupported", "destructive_unsupported"),
        ("Cài app ngân hàng mới", "unsupported", "unsupported_app_install"),
        ("Đọc mã OTP trong SMS", "unsupported", "privacy_sensitive_unsupported"),
        ("Chuyển tiền cho Nam 200 nghìn", "unsupported", "financial_unsupported"),
        ("Viết status mới lên mạng xã hội giúp tôi", "unsupported", "unsupported_social"),
        ("Bật đèn pin", "unsupported", "unsupported_hardware_toggle"),
        ("Chụp màn hình trang này", "unsupported", "unsupported_screenshot"),
        ("Dọn rác bộ nhớ tự động", "unsupported", "unsupported_maintenance"),
        ("Kết nối với tai nghe Bluetooth của tôi", "unsupported", "unsupported_pairing"),
        ("Mở khóa điện thoại", "unsupported", "security_unsupported"),
        ("Ghi âm cuộc gọi đang diễn ra", "unsupported", "privacy_sensitive_unsupported"),
        ("Tắt WiFi ngay", "unsupported", "unsupported_toggle"),
        ("Biên dịch đoạn văn sang tiếng Nhật giùm tôi", "unsupported", "unsupported_translation"),
        ("Tóm tắt email mới nhất", "unsupported", "unsupported_email_read"),
    ]:
        neg(query, status, phenomena)

    for index, row in enumerate(rows, start=1):
        row["id"] = f"fresh{LOCK_DATE}_{index:03d}"
        row["split"] = "fresh_test_locked"

    return rows


def write_ledger(rows: list[dict[str, Any]], tools: dict[str, dict]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "split",
        "source",
        "group",
        "phenomena",
        "query",
        "expected_tool",
        "status",
        "requires_confirmation",
        "required_arguments",
        "expected_arguments_json",
    ]
    with LEDGER_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            exp = row["expected"]
            tool = exp["tool"]
            required = []
            if tool is not None:
                required = [
                    name
                    for name, schema in tools[tool].get("arguments", {}).items()
                    if schema.get("required")
                ]
            writer.writerow(
                {
                    "id": row["id"],
                    "split": row["split"],
                    "source": row["source"],
                    "group": row["group"],
                    "phenomena": row["phenomena"],
                    "query": row["query"],
                    "expected_tool": tool if tool is not None else "",
                    "status": exp.get("status", ""),
                    "requires_confirmation": exp["requires_confirmation"],
                    "required_arguments": "|".join(required),
                    "expected_arguments_json": json.dumps(exp["arguments"], ensure_ascii=False, sort_keys=True),
                }
            )


def audit_leakage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reference_files = [
        path
        for path in sorted(EVAL_DIR.glob("*.jsonl"))
        if path.name != TEST_PATH.name and path.name != "noisy_queries.jsonl"
    ]
    references = []
    for path in reference_files:
        try:
            for ref in load_jsonl(path):
                references.append({"file": path.name, "id": ref.get("id", ""), "query": ref.get("query", "")})
        except Exception as exc:
            references.append({"file": path.name, "id": "__LOAD_ERROR__", "query": str(exc)})

    exact_overlaps = []
    top_matches = []
    for row in rows:
        qn = normalize(row["query"])
        best = {"sequence_ratio": -1.0, "ngram_jaccard": -1.0}
        for ref in references:
            rn = normalize(ref["query"])
            seq = SequenceMatcher(None, qn, rn).ratio()
            jac = jaccard(qn, rn)
            if qn and qn == rn:
                exact_overlaps.append({"fresh_id": row["id"], "reference_file": ref["file"], "reference_id": ref["id"]})
            if (seq, jac) > (best["sequence_ratio"], best["ngram_jaccard"]):
                best = {
                    "fresh_id": row["id"],
                    "fresh_query": row["query"],
                    "reference_file": ref["file"],
                    "reference_id": ref["id"],
                    "reference_query": ref["query"],
                    "sequence_ratio": round(seq, 4),
                    "ngram_jaccard": round(jac, 4),
                }
        top_matches.append(best)

    high_sequence = [m for m in top_matches if m["sequence_ratio"] >= 0.90]
    high_ngram = [m for m in top_matches if m["ngram_jaccard"] >= 0.70]
    return {
        "date": "2026-06-26",
        "fresh_test_path": str(TEST_PATH.relative_to(ROOT)),
        "ledger_path": str(LEDGER_PATH.relative_to(ROOT)),
        "reference_files": [p.name for p in reference_files],
        "fresh_count": len(rows),
        "reference_count": len(references),
        "exact_overlap_count": len(exact_overlaps),
        "exact_overlaps": exact_overlaps,
        "high_sequence_threshold": 0.90,
        "high_sequence_count": len(high_sequence),
        "high_sequence_matches": sorted(high_sequence, key=lambda item: -item["sequence_ratio"])[:50],
        "high_ngram_threshold": 0.70,
        "high_ngram_count": len(high_ngram),
        "high_ngram_matches": sorted(high_ngram, key=lambda item: -item["ngram_jaccard"])[:50],
        "max_sequence_match": max(top_matches, key=lambda item: item["sequence_ratio"]),
        "max_ngram_match": max(top_matches, key=lambda item: item["ngram_jaccard"]),
        "all_top_matches": sorted(top_matches, key=lambda item: -item["sequence_ratio"]),
        "note": "Exact overlaps should remain zero. High similarity rows require manual review before reporting the split as fresh.",
    }


def write_final_config(test_hash: str, ledger_hash: str) -> None:
    config = {
        "locked_at": "2026-06-26",
        "status": "frozen_before_any_fresh_test_model_evaluation",
        "eval_split": str(TEST_PATH.relative_to(ROOT)),
        "eval_sha256": test_hash,
        "ledger": str(LEDGER_PATH.relative_to(ROOT)),
        "ledger_sha256": ledger_hash,
        "selected_model": {
            "version": "v8",
            "rationale": "Chosen before fresh-test evaluation because it was the strongest prior diagnostic configuration, not because of this fresh split.",
            "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
            "adapter_path": "results/adapter_v8",
            "training_file": "data/eval/vi_droidcall_train408_v8.jsonl",
        },
        "retrieval": {
            "type": "hybrid",
            "top_k": 5,
            "alpha": 0.7,
            "alpha_note": "Dense/BM25 interpolation used by vidroidcall_v8_kaggle.ipynb.",
        },
        "prompt": {
            "source": "src/evaluate_ft.py",
            "system_prompt": "SYSTEM_PROMPT + ROBUST_PROMPT_SUFFIX",
            "robust_prompt": True,
        },
        "decoding": {
            "do_sample": False,
            "temperature": 0.0,
            "max_new_tokens": 256,
        },
        "postprocessing": {
            "fix_confirmation_from_schema": True,
            "confirmation_policy": "requires_confirmation is enforced from the fixed tool schema, not trusted from model output.",
        },
        "required_metrics": [
            "canonical_e2e",
            "tool_selection_accuracy",
            "schema_valid_rate",
            "soft_argument_accuracy",
            "requires_confirmation_accuracy",
            "negative_clarification_accuracy",
            "wilson_95_ci",
            "per_schema_e2e",
            "field_level_accuracy",
        ],
        "do_not_use_for": ["alpha_tuning", "top_k_tuning", "prompt_tuning", "augmentation_design", "model_version_selection"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "final_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    tools_list = load_json(TOOLS_PATH)
    tools = {tool["name"]: tool for tool in tools_list}
    rows = build_cases(tools)

    if len(rows) != 126:
        raise AssertionError(f"Expected 126 rows, got {len(rows)}")
    if len({row["id"] for row in rows}) != len(rows):
        raise AssertionError("Duplicate row IDs")
    if len({normalize(row["query"]) for row in rows}) != len(rows):
        raise AssertionError("Duplicate normalized queries")

    tool_counts = Counter(row["expected"]["tool"] for row in rows)
    positive_tools = {tool for tool in tool_counts if tool is not None}
    if positive_tools != set(tools):
        missing = sorted(set(tools) - positive_tools)
        extra = sorted(positive_tools - set(tools))
        raise AssertionError(f"Tool coverage mismatch; missing={missing}, extra={extra}")
    if tool_counts[None] != 30:
        raise AssertionError(f"Expected 30 null-tool cases, got {tool_counts[None]}")

    validator = ToolValidator()
    errors = [(row["id"], validator.validate(row["expected"])) for row in rows if validator.validate(row["expected"])]
    if errors:
        raise AssertionError(f"Invalid gold labels: {errors[:5]}")

    write_jsonl(TEST_PATH, rows)
    write_ledger(rows, tools)

    report = audit_leakage(rows)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    (RESULT_DIR / "leakage_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    test_hash = sha256(TEST_PATH)
    ledger_hash = sha256(LEDGER_PATH)
    write_final_config(test_hash, ledger_hash)

    print(f"Wrote {len(rows)} rows -> {TEST_PATH}")
    print(f"Wrote ledger -> {LEDGER_PATH}")
    print(f"Wrote leakage report -> {RESULT_DIR / 'leakage_report.json'}")
    print(f"Wrote frozen config -> {RESULT_DIR / 'final_config.json'}")
    print(f"Test SHA-256:   {test_hash}")
    print(f"Ledger SHA-256: {ledger_hash}")
    print(f"Exact overlaps: {report['exact_overlap_count']}")
    print(f"High SequenceMatcher >= 0.90: {report['high_sequence_count']}")
    print(f"High char-3 Jaccard >= 0.70: {report['high_ngram_count']}")
    print(f"Groups: {dict(Counter(row['group'] for row in rows))}")
    print(f"Positive tools: {len(positive_tools)}; null-tool cases: {tool_counts[None]}")


if __name__ == "__main__":
    main()
