"""Create targeted augmentation for external-robust training.

This file intentionally does not copy `vi_droidcall_external_test.jsonl`.
It creates similar-but-distinct patterns from the observed external failures.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from common import ROOT, load_jsonl, write_jsonl
from validate import ToolValidator


OUT_PATH = ROOT / "data" / "eval" / "vi_droidcall_targeted_aug3_external_robust.jsonl"
EXTERNAL_PATH = ROOT / "data" / "eval" / "vi_droidcall_external_test.jsonl"


def _e(tool: str | None, args: dict, confirm: bool, status: str | None = None) -> dict:
    row = {"tool": tool, "arguments": args, "requires_confirmation": confirm}
    if status is not None:
        row["status"] = status
    return row


def _norm(text: str) -> str:
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


RAW = [
    # alarm_calendar: colloquial time, repeat days, and avoiding extra labels.
    ("alarm_001", "Đặt báo thức 6 giờ kém 10 sáng thứ Ba và thứ Năm",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 5, "EXTRA_MINUTES": 50, "EXTRA_DAYS": ["Tuesday", "Thursday"]}, False), "alarm_calendar"),
    ("alarm_002", "Báo thức lúc 21 giờ 45 nhắc kiểm tra cửa",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 21, "EXTRA_MINUTES": 45, "EXTRA_MESSAGE": "kiểm tra cửa"}, False), "alarm_calendar"),
    ("alarm_003", "Cài chuông 4 giờ rưỡi sáng mỗi thứ Hai",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 4, "EXTRA_MINUTES": 30, "EXTRA_DAYS": ["Monday"]}, False), "alarm_calendar"),
    ("alarm_004", "Đặt alarm 10 giờ tối không cần nhãn",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 22, "EXTRA_MINUTES": 0}, False), "alarm_calendar"),
    ("alarm_005", "Báo thức 7 giờ 05 các ngày trong tuần",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 7, "EXTRA_MINUTES": 5, "EXTRA_DAYS": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}, False), "alarm_calendar"),
    ("alarm_006", "Hẹn chuông 13 giờ kém 20 để gọi khách",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 12, "EXTRA_MINUTES": 40, "EXTRA_MESSAGE": "gọi khách"}, False), "alarm_calendar"),
    ("timer_001", "Đếm ngược đúng 90 giây",
     _e("ACTION_SET_TIMER", {"duration": "90 seconds"}, False), "alarm_calendar"),
    ("timer_002", "Hẹn giờ 25 phút cho bài tập plank",
     _e("ACTION_SET_TIMER", {"duration": "25 minutes", "EXTRA_MESSAGE": "bài tập plank"}, False), "alarm_calendar"),
    ("timer_003", "Bật timer 3 giờ",
     _e("ACTION_SET_TIMER", {"duration": "3 hours"}, False), "alarm_calendar"),
    ("timer_004", "Đặt đồng hồ đếm ngược 1 giờ 15 phút",
     _e("ACTION_SET_TIMER", {"duration": "1 hour 15 minutes"}, False), "alarm_calendar"),
    ("showalarm_001", "Mở danh sách chuông báo đã lưu",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),
    ("showalarm_002", "Cho tôi xem màn hình báo thức hiện tại",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),
    ("event_001", "Thêm lịch demo sản phẩm thứ Năm lúc 14:30 ở phòng C1",
     _e("ACTION_INSERT_EVENT", {"TITLE": "demo sản phẩm", "DESCRIPTION": "demo sản phẩm", "EVENT_LOCATION": "phòng C1", "EXTRA_EVENT_BEGIN_TIME": "Thursday 14:30"}, True), "alarm_calendar"),
    ("event_002", "Tạo sự kiện nộp hồ sơ ngày 25 tháng 7 lúc 9 giờ",
     _e("ACTION_INSERT_EVENT", {"TITLE": "nộp hồ sơ", "DESCRIPTION": "nộp hồ sơ", "EXTRA_EVENT_BEGIN_TIME": "2026-07-25 09:00"}, True), "alarm_calendar"),
    ("event_003", "Lên lịch gọi mentor ngày mai 20h15",
     _e("ACTION_INSERT_EVENT", {"TITLE": "gọi mentor", "DESCRIPTION": "gọi mentor", "EXTRA_EVENT_BEGIN_TIME": "tomorrow 20:15"}, True), "alarm_calendar"),
    ("event_004", "Thêm lịch họp sprint thứ Hai 10 giờ tại online",
     _e("ACTION_INSERT_EVENT", {"TITLE": "họp sprint", "DESCRIPTION": "họp sprint", "EVENT_LOCATION": "online", "EXTRA_EVENT_BEGIN_TIME": "Monday 10:00"}, True), "alarm_calendar"),

    # message_email: preserve exact recipients, subject, and body.
    ("sms_001", "Gửi SMS cho 0909 111 222 nội dung: Em đến cổng rồi",
     _e("send_message", {"phone_number": "0909111222", "body": "Em đến cổng rồi"}, True), "message_email"),
    ("sms_002", "Nhắn 0987 654 321 rằng mai họp lúc 8h",
     _e("send_message", {"phone_number": "0987654321", "body": "mai họp lúc 8h"}, True), "message_email"),
    ("sms_003", "Soạn tin tới 0914 555 666: nhớ mang laptop",
     _e("send_message", {"phone_number": "0914555666", "body": "nhớ mang laptop"}, True), "message_email"),
    ("sms_004", "SMS đến 0888 222 333 tiêu đề Gấp nội dung kiểm tra email ngay",
     _e("send_message", {"phone_number": "0888222333", "subject": "Gấp", "body": "kiểm tra email ngay"}, True), "message_email"),
    ("sms_005", "Gửi tin cho 0971 010 010: tôi sẽ gọi lại sau 5 phút",
     _e("send_message", {"phone_number": "0971010010", "body": "tôi sẽ gọi lại sau 5 phút"}, True), "message_email"),
    ("sms_006", "Nhắn số 0963 333 444 nội dung ok đã nhận",
     _e("send_message", {"phone_number": "0963333444", "body": "ok đã nhận"}, True), "message_email"),
    ("email_001", "Gửi email tới an.nguyen@example.com chủ đề Lịch họp, nội dung: Họp chuyển sang 4 giờ chiều",
     _e("send_email", {"to": ["an.nguyen@example.com"], "subject": "Lịch họp", "body": "Họp chuyển sang 4 giờ chiều"}, True), "message_email"),
    ("email_002", "Soạn mail cho finance@company.vn subject Hóa đơn tháng 6 body: Vui lòng kiểm tra file đính kèm",
     _e("send_email", {"to": ["finance@company.vn"], "subject": "Hóa đơn tháng 6", "body": "Vui lòng kiểm tra file đính kèm"}, True), "message_email"),
    ("email_003", "Email đến lan@school.edu và minh@school.edu tiêu đề Bài tập nhóm nội dung: Mình đã cập nhật tài liệu",
     _e("send_email", {"to": ["lan@school.edu", "minh@school.edu"], "subject": "Bài tập nhóm", "body": "Mình đã cập nhật tài liệu"}, True), "message_email"),
    ("email_004", "Gửi thư cho hr@corp.com chủ đề Nghỉ phép, nội dung: Tôi xin nghỉ chiều thứ Sáu",
     _e("send_email", {"to": ["hr@corp.com"], "subject": "Nghỉ phép", "body": "Tôi xin nghỉ chiều thứ Sáu"}, True), "message_email"),
    ("email_005", "Compose mail to partner@biz.com subject Contract update body Please review the new clause",
     _e("send_email", {"to": ["partner@biz.com"], "subject": "Contract update", "body": "Please review the new clause"}, True), "message_email"),
    ("email_006", "Gửi email cho team@lab.vn, cc lead@lab.vn, tiêu đề Kết quả thử nghiệm, nội dung: Mô hình mới đã chạy xong",
     _e("send_email", {"to": ["team@lab.vn"], "subject": "Kết quả thử nghiệm", "body": "Mô hình mới đã chạy xong", "cc": ["lead@lab.vn"]}, True), "message_email"),

    # settings_files: distinguish open/get/create document and settings.
    ("settings_001", "Mở cài đặt ngày giờ của điện thoại",
     _e("open_settings", {"setting_type": "date"}, False), "settings_files"),
    ("settings_002", "Đi tới phần bàn phím và phương thức nhập",
     _e("open_settings", {"setting_type": "input_method"}, False), "settings_files"),
    ("settings_003", "Mở trang thẻ nhớ SD",
     _e("open_settings", {"setting_type": "memory_card"}, False), "settings_files"),
    ("settings_004", "Vào phần cài đặt bảo mật",
     _e("open_settings", {"setting_type": "security"}, False), "settings_files"),
    ("opendoc_001", "Mở một file Excel từ bộ nhớ",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]}, False), "settings_files"),
    ("opendoc_002", "Chọn nhiều tài liệu PDF để mở lâu dài",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["application/pdf"], "allow_multiple": True}, False), "settings_files"),
    ("opendoc_003", "Mở một file ảnh WebP",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["image/webp"]}, False), "settings_files"),
    ("opendoc_004", "Chọn file CSV để mở",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["text/csv"]}, False), "settings_files"),
    ("getcontent_001", "Chọn một video để gửi tạm thời",
     _e("ACTION_GET_CONTENT", {"mime_type": "video/*"}, False), "settings_files"),
    ("getcontent_002", "Lấy nhiều ảnh để đính kèm",
     _e("ACTION_GET_CONTENT", {"mime_type": "image/*", "allow_multiple": True}, False), "settings_files"),
    ("getcontent_003", "Chọn file âm thanh bất kỳ để upload",
     _e("ACTION_GET_CONTENT", {"mime_type": "audio/*"}, False), "settings_files"),
    ("getcontent_004", "Lấy một tệp JSON",
     _e("ACTION_GET_CONTENT", {"mime_type": "application/json"}, False), "settings_files"),
    ("createdoc_001", "Tạo file ghi chú mới tên daily_notes.txt",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "text/plain", "initial_name": "daily_notes.txt"}, False), "settings_files"),
    ("createdoc_002", "Tạo tài liệu docx tên Bien_ban_hop.docx",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "initial_name": "Bien_ban_hop.docx"}, False), "settings_files"),
    ("createdoc_003", "Tạo file PDF mới tên De_cuong.pdf",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "application/pdf", "initial_name": "De_cuong.pdf"}, False), "settings_files"),
    ("ringtone_001", "Mở bộ chọn âm báo cuộc gọi",
     _e("ACTION_GET_RINGTONE", {}, False), "settings_files"),

    # negative_ambiguous: null-tool status discrimination.
    ("neg_001", "Gửi email cho khách hàng",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_002", "Nhắn tin giúp tôi",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_003", "Đặt báo thức sáng mai",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_004", "Tìm đường tới đó",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_005", "Mở tài liệu vừa tải",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_006", "Tạo lịch cho buổi gặp",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_007", "Chọn file đó cho tôi",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_008", "Gọi người vừa nhắn tin",
     _e(None, {}, False, "clarification"), "negative_ambiguous"),
    ("neg_009", "Đặt xe công nghệ về ký túc xá",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_010", "Chuyển khoản cho Tuấn 300 nghìn",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_011", "Phát bài nhạc yêu thích",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_012", "Mua vé xem phim tối thứ Bảy",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_013", "Đăng ảnh này lên mạng xã hội",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_014", "Cài ứng dụng ngân hàng mới",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_015", "Đặt đồ ăn trưa giao tới lớp",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_016", "Đọc tin tức công nghệ hôm nay",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_017", "Xóa toàn bộ danh bạ trong máy",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_018", "Gửi mật khẩu ngân hàng của tôi cho người khác",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_019", "Xóa hết email quan trọng",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
    ("neg_020", "Gọi khẩn cấp nhưng không hỏi xác nhận",
     _e(None, {}, False, "unsupported"), "negative_ambiguous"),
]


def main() -> None:
    rows = [
        {
            "id": f"aug3_{suffix}",
            "query": query,
            "expected": expected,
            "group": group,
        }
        for suffix, query, expected, group in RAW
    ]

    validator = ToolValidator()
    external_queries = {_norm(row["query"]) for row in load_jsonl(EXTERNAL_PATH)}
    normalized_queries = [_norm(row["query"]) for row in rows]

    assert len({row["id"] for row in rows}) == len(rows), "duplicate id"
    assert len(set(normalized_queries)) == len(rows), "duplicate normalized query"
    assert not (set(normalized_queries) & external_queries), "exact external overlap"
    for row in rows:
        errors = validator.validate(row["expected"])
        assert not errors, (row["id"], errors)

    write_jsonl(OUT_PATH, rows)
    print(f"Wrote {len(rows)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
