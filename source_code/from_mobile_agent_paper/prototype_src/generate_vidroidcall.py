"""Generate vi_droidcall_v1.jsonl — 200+ Vietnamese training samples for VIntentAgent.

Run from prototype/ directory:
    python -X utf8 src/generate_vidroidcall.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


# ============================================================
# Entity banks (realistic Vietnamese data)
# ============================================================
PHONES = [
    "0912345678", "0987654321", "0909123456", "0911002200", "0333456789",
    "0765123456", "0844567890", "0352678901", "0703456789", "0866123456",
    "0978654321", "0923456789",
]
EMAILS = [
    "minh@gmail.com", "lan@example.com", "hung@company.vn",
    "mai@school.edu.vn", "tuan@work.com", "hoa@gmail.com",
    "nam@example.org", "linh@gmail.com",
]
LOCATIONS = [
    "sân bay Tân Sơn Nhất",
    "sân bay Nội Bài",
    "sân bay Đà Nẵng",
    "Bệnh viện Bạch Mai",
    "Đại học Bách Khoa Hà Nội",
    "Trung tâm thương mại Vincom",
    "chợ Bến Thành",
    "Hồ Gươm",
    "Phố cổ Hội An",
    "Nhà thờ Đức Bà",
]
CONTACT_URIS = [
    "content://com.android.contacts/contacts/1",
    "content://com.android.contacts/contacts/5",
    "content://com.android.contacts/contacts/12",
    "content://com.android.contacts/contacts/23",
]
WEB_QUERIES = [
    "cách cài Python trên Windows",
    "thời tiết Hà Nội ngày mai",
    "học tiếng Anh giao tiếp online miễn phí",
    "nhà hàng ngon gần đây",
    "lịch chiếu phim tuần này",
    "hướng dẫn nấu bún bò Huế",
    "giá vé tàu Hà Nội Đà Nẵng",
    "cách chuyển file từ điện thoại sang máy tính",
    "học lập trình Python cơ bản",
    "cách giảm cân hiệu quả",
]

# ============================================================
# Helpers
# ============================================================
SAMPLES: list[dict[str, Any]] = []
_counters: dict[str, int] = {}


def uid(prefix: str) -> str:
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return f"vdc_{prefix}_{_counters[prefix]:03d}"


def add(
    sample_id: str,
    group: str,
    query: str,
    tool: str | None,
    arguments: dict[str, Any],
    confirmation: bool,
    status: str | None = None,
) -> None:
    expected: dict[str, Any] = {
        "tool": tool,
        "arguments": arguments,
        "requires_confirmation": confirmation,
    }
    if status:
        expected["status"] = status
    SAMPLES.append({"id": sample_id, "group": group, "query": query, "expected": expected})


# ============================================================
# 1. ACTION_SET_ALARM  (15 samples)
# ============================================================
G_AC = "alarm_calendar"
_alarm: list[tuple[str, int, int, dict[str, Any]]] = [
    ("Đặt báo thức 5 giờ sáng", 5, 0, {}),
    ("Báo thức 5 giờ 30 nhãn tập gym", 5, 30, {"EXTRA_MESSAGE": "tập gym"}),
    ("Cài báo thức lúc 6 giờ để uống thuốc", 6, 0, {"EXTRA_MESSAGE": "uống thuốc"}),
    ("Đặt báo thức lúc 6 giờ 30 sáng nhãn ăn sáng", 6, 30, {"EXTRA_MESSAGE": "ăn sáng"}),
    ("Nhắc tôi dậy lúc 7 giờ", 7, 0, {}),
    ("Đặt alarm 7 giờ 15 sáng nhãn đi học", 7, 15, {"EXTRA_MESSAGE": "đi học"}),
    ("Báo thức lúc 8 giờ sáng", 8, 0, {}),
    ("Đặt báo thức 9 giờ nhãn họp online", 9, 0, {"EXTRA_MESSAGE": "họp online"}),
    ("Hẹn báo thức 10 giờ sáng", 10, 0, {}),
    ("Báo thức 2 giờ chiều nhãn gặp khách hàng", 14, 0, {"EXTRA_MESSAGE": "gặp khách hàng"}),
    ("Đặt báo thức lúc 4 giờ 30 sáng", 4, 30, {}),
    ("Cài alarm 6 giờ 45 nhãn đi làm", 6, 45, {"EXTRA_MESSAGE": "đi làm"}),
    ("Đặt báo thức 7 giờ sáng cho tôi", 7, 0, {}),
    ("Báo thức lúc 8 giờ 30 nhãn nộp báo cáo", 8, 30, {"EXTRA_MESSAGE": "nộp báo cáo"}),
    ("Cài báo thức 5 giờ nhãn chạy bộ", 5, 0, {"EXTRA_MESSAGE": "chạy bộ"}),
]
for query, h, m, extra in _alarm:
    args: dict[str, Any] = {"EXTRA_HOUR": h, "EXTRA_MINUTES": m}
    args.update(extra)
    add(uid("alarm"), G_AC, query, "ACTION_SET_ALARM", args, False)

# ============================================================
# 2. ACTION_SHOW_ALARMS  (6 samples)
# ============================================================
for query in [
    "Cho xem danh sách báo thức",
    "Liệt kê các báo thức đang có",
    "Hiện tất cả báo thức",
    "Xem báo thức",
    "Có những báo thức nào đang bật?",
    "Kiểm tra báo thức của tôi",
]:
    add(uid("show_alarms"), G_AC, query, "ACTION_SHOW_ALARMS", {}, False)

# ============================================================
# 3. ACTION_SET_TIMER  (20 samples)
# ============================================================
_timer: list[tuple[str, str, dict[str, Any]]] = [
    ("Hẹn giờ 5 phút", "5 minutes", {}),
    ("Đặt timer 8 phút để luộc trứng", "8 minutes", {"EXTRA_MESSAGE": "luộc trứng"}),
    ("Hẹn giờ 10 phút để nghỉ giải lao", "10 minutes", {"EXTRA_MESSAGE": "nghỉ giải lao"}),
    ("Đặt đếm ngược 15 phút để tắt bếp", "15 minutes", {"EXTRA_MESSAGE": "tắt bếp"}),
    ("Hẹn 20 phút", "20 minutes", {}),
    ("Đếm ngược 30 phút để lấy đồ khỏi máy giặt", "30 minutes", {"EXTRA_MESSAGE": "lấy đồ khỏi máy giặt"}),
    ("Hẹn giờ 45 phút", "45 minutes", {}),
    ("Timer 1 giờ để uống thuốc", "1 hours", {"EXTRA_MESSAGE": "uống thuốc"}),
    ("Hẹn giờ 2 phút để pha trà", "2 minutes", {"EXTRA_MESSAGE": "pha trà"}),
    ("Đặt bộ đếm 90 giây", "90 seconds", {}),
    ("Hẹn 3 phút để rửa mặt", "3 minutes", {"EXTRA_MESSAGE": "rửa mặt"}),
    ("Đặt timer 25 phút kỹ thuật Pomodoro", "25 minutes", {"EXTRA_MESSAGE": "kỹ thuật Pomodoro"}),
    ("Hẹn giờ 5 phút nấu mì", "5 minutes", {"EXTRA_MESSAGE": "nấu mì"}),
    ("Đặt đồng hồ đếm ngược 40 phút tập thể dục", "40 minutes", {"EXTRA_MESSAGE": "tập thể dục"}),
    ("Set timer 2 tiếng tắt máy tính", "2 hours", {"EXTRA_MESSAGE": "tắt máy tính"}),
    ("Hẹn 20 phút cho bánh nướng", "20 minutes", {"EXTRA_MESSAGE": "bánh nướng"}),
    ("Timer 15 phút sạc điện thoại", "15 minutes", {"EXTRA_MESSAGE": "sạc điện thoại"}),
    ("Đặt timer 12 phút nấu phở", "12 minutes", {"EXTRA_MESSAGE": "nấu phở"}),
    ("Hẹn giờ 6 phút pha cà phê", "6 minutes", {"EXTRA_MESSAGE": "pha cà phê"}),
    ("Đếm ngược 35 phút nghỉ trưa", "35 minutes", {"EXTRA_MESSAGE": "nghỉ trưa"}),
]
for query, duration, extra in _timer:
    targs: dict[str, Any] = {"duration": duration}
    targs.update(extra)
    add(uid("timer"), G_AC, query, "ACTION_SET_TIMER", targs, False)

# ============================================================
# 4. ACTION_INSERT_EVENT  (15 samples)
# ============================================================
_event: list[tuple[str, str, str, str | None, str | None]] = [
    ("Thêm lịch họp nhóm lúc 9 giờ sáng mai", "họp nhóm", "họp nhóm", None, "tomorrow 09:00"),
    ("Thêm sự kiện gặp khách hàng lúc 2 giờ chiều mai tại văn phòng", "gặp khách hàng", "gặp khách hàng", "văn phòng", "tomorrow 14:00"),
    ("Ghi lịch sinh nhật Lan vào ngày mai", "sinh nhật Lan", "sinh nhật Lan", None, None),
    ("Thêm lịch khám bác sĩ lúc 8 giờ sáng mai tại bệnh viện", "khám bác sĩ", "khám bác sĩ", "bệnh viện", "tomorrow 08:00"),
    ("Tạo sự kiện hội thảo online lúc 3 giờ chiều", "hội thảo online", "hội thảo online", None, "15:00"),
    ("Thêm lịch họp ban giám đốc mai lúc 10 giờ tại phòng họp lớn", "họp ban giám đốc", "họp ban giám đốc", "phòng họp lớn", "tomorrow 10:00"),
    ("Ghi vào lịch dự tiệc lúc 6 giờ tối", "dự tiệc", "dự tiệc", None, "18:00"),
    ("Thêm sự kiện báo cáo tiến độ dự án lúc 4 giờ chiều mai", "báo cáo tiến độ dự án", "báo cáo tiến độ dự án", None, "tomorrow 16:00"),
    ("Tạo lịch cuộc họp lúc 9 giờ sáng ngày mai", "cuộc họp", "cuộc họp", None, "tomorrow 09:00"),
    ("Thêm sự kiện sinh nhật anh Nam vào thứ 6 tuần này", "sinh nhật anh Nam", "sinh nhật anh Nam", None, None),
    ("Đặt lịch hẹn khám bác sĩ lúc 3 giờ chiều ngày 15", "hẹn khám bác sĩ", "hẹn khám bác sĩ", None, "15:00"),
    ("Tạo nhắc nhở họp team lúc 10 giờ sáng tại phòng 203", "họp team", "họp team", "phòng 203", "10:00"),
    ("Thêm lịch họp phụ huynh lúc 7 giờ tối thứ 5", "họp phụ huynh", "họp phụ huynh", None, "19:00"),
    ("Tạo event seminar kỹ thuật lúc 2 giờ chiều thứ 2", "seminar kỹ thuật", "seminar kỹ thuật", None, "14:00"),
    ("Đặt lịch dã ngoại cuối tuần lúc 8 giờ sáng tại công viên", "dã ngoại cuối tuần", "dã ngoại cuối tuần", "công viên", "08:00"),
]
for query, title, desc, location, begin_time in _event:
    eargs: dict[str, Any] = {"TITLE": title, "DESCRIPTION": desc}
    if location:
        eargs["EVENT_LOCATION"] = location
    if begin_time:
        eargs["EXTRA_EVENT_BEGIN_TIME"] = begin_time
    add(uid("event"), G_AC, query, "ACTION_INSERT_EVENT", eargs, True)

# ============================================================
# 5. ACTION_INSERT_CONTACT  (9 samples)
# ============================================================
G_CC = "contact_call"
_ins: list[tuple[str, str, str, str | None]] = [
    ("Thêm liên hệ Minh số 0912345678", "Minh", "0912345678", None),
    ("Lưu số 0987654321 tên Lan", "Lan", "0987654321", None),
    ("Tạo liên hệ mới Hùng số 0333456789", "Hùng", "0333456789", None),
    ("Thêm liên hệ Nam số 0765123456 email nam@example.com", "Nam", "0765123456", "nam@example.com"),
    ("Lưu liên hệ cô Mai số 0909123456", "Mai", "0909123456", None),
    ("Thêm bạn Linh vào danh bạ số 0844567890", "Linh", "0844567890", None),
    ("Tạo liên hệ anh Tuấn điện thoại 0911002200", "Tuấn", "0911002200", None),
    ("Lưu số 0866123456 của chị Hoa vào danh bạ", "Hoa", "0866123456", None),
    ("Thêm danh bạ mới tên Phong số 0978654321", "Phong", "0978654321", None),
]
for query, name, phone, email in _ins:
    info: dict[str, Any] = {"name": name, "phone": phone}
    if email:
        info["email"] = email
    add(uid("contact_insert"), G_CC, query, "ACTION_INSERT_CONTACT", {"contact_info": info}, True)

# ============================================================
# 6. get_contact_info  (9 samples)
# ============================================================
_lookup: list[tuple[str, str, str]] = [
    ("Tìm số điện thoại của Minh trong danh bạ", "Minh", "phone"),
    ("Số điện thoại của chị Lan là gì?", "Lan", "phone"),
    ("Cho tôi email của anh Hùng", "Hùng", "email"),
    ("Email của bạn Nam trong danh bạ?", "Nam", "email"),
    ("Địa chỉ của cô Mai trong danh bạ", "Mai", "address"),
    ("Tìm số của Tuấn", "Tuấn", "phone"),
    ("Tra số điện thoại anh Thành", "Thành", "phone"),
    ("Tìm email của chị Nga trong danh bạ", "Nga", "email"),
    ("Số điện thoại của bạn Thu là bao nhiêu?", "Thu", "phone"),
]
for query, name, key in _lookup:
    add(uid("contact_lookup"), G_CC, query, "get_contact_info", {"name": name, "key": key}, False)

# ============================================================
# 7. get_contact_info_from_uri  (4 samples)
# ============================================================
_uri_lookup = [
    (f"Lấy số điện thoại từ liên hệ {CONTACT_URIS[0]}", CONTACT_URIS[0], "phone"),
    (f"Tra email của liên hệ {CONTACT_URIS[1]}", CONTACT_URIS[1], "email"),
    (f"Địa chỉ liên hệ tại {CONTACT_URIS[2]}", CONTACT_URIS[2], "address"),
    (f"Lấy số điện thoại liên hệ {CONTACT_URIS[3]}", CONTACT_URIS[3], "phone"),
]
for query, uri, key in _uri_lookup:
    add(uid("contact_uri"), G_CC, query, "get_contact_info_from_uri", {"contact_uri": uri, "key": key}, False)

# ============================================================
# 8. ACTION_VIEW_CONTACT  (4 samples)
# ============================================================
_view_q = [
    f"Xem thông tin liên hệ {CONTACT_URIS[0]}",
    f"Mở liên hệ {CONTACT_URIS[1]}",
    f"Hiện chi tiết liên hệ {CONTACT_URIS[2]}",
    f"Cho tôi xem liên hệ {CONTACT_URIS[3]}",
]
for q, uri in zip(_view_q, CONTACT_URIS):
    add(uid("view_contact"), G_CC, q, "ACTION_VIEW_CONTACT", {"contact_uri": uri}, False)

# ============================================================
# 9. ACTION_EDIT_CONTACT  (4 samples)
# ============================================================
_edit_q = [
    f"Sửa thông tin liên hệ {CONTACT_URIS[0]}",
    f"Cập nhật liên hệ {CONTACT_URIS[1]}",
    f"Chỉnh sửa liên hệ {CONTACT_URIS[2]}",
    f"Mở giao diện sửa liên hệ {CONTACT_URIS[3]}",
]
for q, uri in zip(_edit_q, CONTACT_URIS):
    add(uid("edit_contact"), G_CC, q, "ACTION_EDIT_CONTACT", {"contact_uri": uri}, True)

# ============================================================
# 10. ACTION_PICK  (8 samples)
# ============================================================
_pick: list[tuple[str, str]] = [
    ("Mở danh sách để tôi chọn một số điện thoại", "PHONE"),
    ("Cho tôi chọn một địa chỉ email từ danh bạ", "EMAIL"),
    ("Chọn một địa chỉ từ danh bạ", "ADDRESS"),
    ("Mở danh bạ để chọn liên hệ", "ALL"),
    ("Tôi muốn chọn một liên hệ", "ALL"),
    ("Chọn số điện thoại từ danh bạ", "PHONE"),
    ("Mở để chọn một email từ danh sách", "EMAIL"),
    ("Cho tôi chọn một địa chỉ", "ADDRESS"),
]
for query, data_type in _pick:
    add(uid("pick"), G_CC, query, "ACTION_PICK", {"data_type": data_type}, False)

# ============================================================
# 11. dial  (10 samples)
# ============================================================
_dial_q = [
    f"Gọi số {PHONES[0]}",
    f"Gọi điện tới {PHONES[1]}",
    f"Quay số {PHONES[2]}",
    f"Gọi {PHONES[3]} giúp tôi",
    f"Gọi ngay cho số {PHONES[4]}",
    f"Cho tôi gọi {PHONES[5]}",
    f"Quay số điện thoại {PHONES[6]}",
    f"Gọi số này cho tôi: {PHONES[7]}",
    f"Mở trình quay số {PHONES[8]}",
    f"Tôi muốn gọi cho số {PHONES[9]}",
]
for i, q in enumerate(_dial_q):
    add(uid("dial"), G_CC, q, "dial", {"phone_number": PHONES[i]}, True)

# ============================================================
# 12. send_message  (18 samples)
# ============================================================
G_ME = "message_email"
_sms: list[tuple[str, str, str, str]] = [
    # Original 9
    (f"Nhắn {PHONES[0]} rằng tôi sẽ đến muộn 15 phút", PHONES[0], "", "tôi sẽ đến muộn 15 phút"),
    (f"Soạn tin cho {PHONES[1]} nội dung đang trên đường", PHONES[1], "", "đang trên đường"),
    (f"Gửi SMS tới {PHONES[2]}: nhớ mang tài liệu ngày mai", PHONES[2], "", "nhớ mang tài liệu ngày mai"),
    (f"Nhắn tin {PHONES[3]} tiêu đề cuộc họp nội dung họp lúc 9 giờ", PHONES[3], "cuộc họp", "họp lúc 9 giờ"),
    (f"Soạn tin nhắn cho {PHONES[4]} nội dung xin lỗi tôi bận", PHONES[4], "", "xin lỗi tôi bận"),
    (f"Nhắn {PHONES[5]} rằng cảm ơn bạn rất nhiều", PHONES[5], "", "cảm ơn bạn rất nhiều"),
    (f"Gửi tin nhắn cho {PHONES[6]} tiêu đề nhắc nhở nội dung đừng quên nộp báo cáo", PHONES[6], "nhắc nhở", "đừng quên nộp báo cáo"),
    (f"Nhắn {PHONES[7]} rằng tôi sẽ gọi lại sau", PHONES[7], "", "tôi sẽ gọi lại sau"),
    (f"Soạn tin tới {PHONES[8]} nội dung hẹn gặp lúc 3 giờ chiều", PHONES[8], "", "hẹn gặp lúc 3 giờ chiều"),
    # New 9 — subject rỗng (6 mẫu)
    (f"Nhắn {PHONES[9]} là tôi đang trên đường về", PHONES[9], "", "tôi đang trên đường về"),
    (f"Nhắn tin cho {PHONES[10]} rằng họp bị dời sang chiều", PHONES[10], "", "họp bị dời sang chiều"),
    (f"Gửi SMS tới {PHONES[11]}: cảm ơn bạn đã giúp đỡ", PHONES[11], "", "cảm ơn bạn đã giúp đỡ"),
    ("Nhắn 0765123456 rằng tôi sẽ gọi lại lúc 3 giờ", "0765123456", "", "tôi sẽ gọi lại lúc 3 giờ"),
    ("Nhắn tin 0844567890 nội dung đừng quên mang laptop", "0844567890", "", "đừng quên mang laptop"),
    ("Soạn tin nhắn cho 0352678901 nội dung anh ơi em bị trễ", "0352678901", "", "anh ơi em bị trễ"),
    # New — có subject rõ ràng (3 mẫu)
    ("Nhắn 0703456789 tiêu đề nhắc nợ nội dung nhớ trả tiền tháng này", "0703456789", "nhắc nợ", "nhớ trả tiền tháng này"),
    ("Soạn tin cho 0866123456 tiêu đề lịch họp nội dung họp lúc 2 giờ chiều", "0866123456", "lịch họp", "họp lúc 2 giờ chiều"),
    ("Gửi tin nhắn tới 0978654321 tiêu đề chúc mừng nội dung chúc mừng sinh nhật bạn", "0978654321", "chúc mừng", "chúc mừng sinh nhật bạn"),
]
for query, phone, subject, body in _sms:
    add(uid("sms"), G_ME, query, "send_message", {"phone_number": phone, "subject": subject, "body": body}, True)

# ============================================================
# 13. send_email  (15 samples)
# ============================================================
_email: list[tuple[str, list[str], str, str]] = [
    # Original 8
    (f"Gửi email cho {EMAILS[0]}, tiêu đề Báo cáo tuần, nội dung Em gửi báo cáo tuần này", [EMAILS[0]], "Báo cáo tuần", "Em gửi báo cáo tuần này"),
    (f"Soạn thư tới {EMAILS[1]} với chủ đề Lịch họp, nội dung Họp lúc 9 giờ sáng thứ Hai", [EMAILS[1]], "Lịch họp", "Họp lúc 9 giờ sáng thứ Hai"),
    (f"Gửi mail {EMAILS[2]} tiêu đề Xin phép nghỉ, nội dung Em xin phép nghỉ hôm nay vì ốm", [EMAILS[2]], "Xin phép nghỉ", "Em xin phép nghỉ hôm nay vì ốm"),
    (f"Gửi email tới {EMAILS[0]} và {EMAILS[1]}, tiêu đề Thông báo, nội dung Buổi học bị dời", [EMAILS[0], EMAILS[1]], "Thông báo", "Buổi học bị dời"),
    (f"Soạn email cho {EMAILS[3]}, chủ đề Kết quả thi, nội dung Điểm thi đã có trên cổng thông tin", [EMAILS[3]], "Kết quả thi", "Điểm thi đã có trên cổng thông tin"),
    (f"Gửi thư tới {EMAILS[4]} tiêu đề Xác nhận đơn hàng nội dung Đơn hàng của bạn đã được xác nhận", [EMAILS[4]], "Xác nhận đơn hàng", "Đơn hàng của bạn đã được xác nhận"),
    (f"Email cho {EMAILS[5]}, tiêu đề Tài liệu họp, nội dung Đính kèm tài liệu buổi họp tuần tới", [EMAILS[5]], "Tài liệu họp", "Đính kèm tài liệu buổi họp tuần tới"),
    (f"Soạn thư gửi {EMAILS[6]} chủ đề Chúc mừng nội dung Chúc mừng sinh nhật bạn", [EMAILS[6]], "Chúc mừng", "Chúc mừng sinh nhật bạn"),
    # New 7 — phân biệt rõ email vs SMS, nhiều recipient
    ("Gửi email tới minh@gmail.com và lan@example.com chủ đề thông báo nội dung buổi họp bị hoãn", ["minh@gmail.com", "lan@example.com"], "thông báo", "buổi họp bị hoãn"),
    ("Soạn email cho hung@company.vn tiêu đề xin phép nghỉ nội dung em xin nghỉ ngày mai vì bận việc gia đình", ["hung@company.vn"], "xin phép nghỉ", "em xin nghỉ ngày mai vì bận việc gia đình"),
    ("Gửi thư tới mai@school.edu.vn chủ đề kết quả học tập nội dung điểm thi học kỳ đã được cập nhật", ["mai@school.edu.vn"], "kết quả học tập", "điểm thi học kỳ đã được cập nhật"),
    ("Email cho tuan@work.com và hoa@gmail.com tiêu đề lịch dự án nội dung deadline dự án là thứ 6 tuần này", ["tuan@work.com", "hoa@gmail.com"], "lịch dự án", "deadline dự án là thứ 6 tuần này"),
    ("Gửi email tới nam@example.org tiêu đề mời họp nội dung kính mời anh tham dự buổi họp lúc 9 giờ sáng thứ 2", ["nam@example.org"], "mời họp", "kính mời anh tham dự buổi họp lúc 9 giờ sáng thứ 2"),
    ("Soạn thư gửi linh@gmail.com chủ đề tài liệu họp nội dung gửi kèm tài liệu buổi họp tuần tới", ["linh@gmail.com"], "tài liệu họp", "gửi kèm tài liệu buổi họp tuần tới"),
    ("Gửi email cho minh@gmail.com hung@company.vn mai@school.edu.vn chủ đề thông báo lịch nghỉ lễ nội dung công ty nghỉ lễ từ ngày 30/4 đến 2/5", ["minh@gmail.com", "hung@company.vn", "mai@school.edu.vn"], "thông báo lịch nghỉ lễ", "công ty nghỉ lễ từ ngày 30/4 đến 2/5"),
]
for query, to, subject, body in _email:
    add(uid("email"), G_ME, query, "send_email", {"to": to, "subject": subject, "body": body}, True)

# ============================================================
# 14. web_search  (10 samples)
# ============================================================
G_MC = "map_web_camera"
_web: list[tuple[str, str]] = [
    (f"Tìm kiếm {WEB_QUERIES[0]}", WEB_QUERIES[0]),
    (f"Tìm trên Google {WEB_QUERIES[1]}", WEB_QUERIES[1]),
    (f"Google {WEB_QUERIES[2]}", WEB_QUERIES[2]),
    (f"Tìm thông tin về {WEB_QUERIES[3]}", WEB_QUERIES[3]),
    (f"Search {WEB_QUERIES[4]}", WEB_QUERIES[4]),
    (f"Tìm trên mạng: {WEB_QUERIES[5]}", WEB_QUERIES[5]),
    (f"Hãy tìm kiếm {WEB_QUERIES[6]}", WEB_QUERIES[6]),
    (f"Tìm trên Google {WEB_QUERIES[7]}", WEB_QUERIES[7]),
    (f"Tra Google xem {WEB_QUERIES[8]}", WEB_QUERIES[8]),
    (f"Tìm kiếm trên Google: {WEB_QUERIES[9]}", WEB_QUERIES[9]),
]
for query, q in _web:
    add(uid("web"), G_MC, query, "web_search", {"query": q, "engine": "google"}, False)

# ============================================================
# 15. search_location  (10 samples)
# ============================================================
_loc: list[tuple[str, str]] = [
    (f"Tìm {LOCATIONS[0]} trên bản đồ", LOCATIONS[0]),
    (f"Chỉ đường tới {LOCATIONS[1]}", LOCATIONS[1]),
    (f"Tìm đường đến {LOCATIONS[2]}", LOCATIONS[2]),
    (f"Tìm {LOCATIONS[3]} trên bản đồ", LOCATIONS[3]),
    (f"Chỉ đường tới {LOCATIONS[4]}", LOCATIONS[4]),
    (f"Mở bản đồ tìm {LOCATIONS[5]}", LOCATIONS[5]),
    (f"Tìm vị trí {LOCATIONS[6]} trên Google Maps", LOCATIONS[6]),
    (f"Chỉ đường tới {LOCATIONS[7]}", LOCATIONS[7]),
    (f"Tìm {LOCATIONS[8]} trên bản đồ", LOCATIONS[8]),
    (f"Chỉ đường đến {LOCATIONS[9]}", LOCATIONS[9]),
]
for query, loc in _loc:
    add(uid("location"), G_MC, query, "search_location", {"query": loc}, False)

# ============================================================
# 16. INTENT_ACTION_STILL_IMAGE_CAMERA  (6 samples)
# ============================================================
for query in [
    "Mở máy ảnh",
    "Bật camera",
    "Mở camera để chụp hình",
    "Cho tôi vào camera",
    "Mở ứng dụng camera",
    "Tôi muốn chụp hình, mở camera lên",
]:
    add(uid("camera_open"), G_MC, query, "INTENT_ACTION_STILL_IMAGE_CAMERA", {}, False)

# ============================================================
# 17. ACTION_IMAGE_CAPTURE  (5 samples)
# ============================================================
for query in [
    "Chụp một bức ảnh ngay",
    "Chụp ảnh",
    "Chụp hình ngay bây giờ",
    "Chụp một cái ảnh",
    "Chụp ảnh và lưu lại",
]:
    add(uid("photo"), G_MC, query, "ACTION_IMAGE_CAPTURE", {}, False)

# ============================================================
# 18. INTENT_ACTION_VIDEO_CAMERA  (5 samples)
# ============================================================
for query in [
    "Mở chế độ quay phim",
    "Bật camera quay video",
    "Mở video camera",
    "Chuyển sang chế độ quay",
    "Mở camera ở chế độ video",
]:
    add(uid("video_open"), G_MC, query, "INTENT_ACTION_VIDEO_CAMERA", {}, False)

# ============================================================
# 19. ACTION_VIDEO_CAPTURE  (5 samples)
# ============================================================
for query in [
    "Quay một video",
    "Bắt đầu quay video",
    "Quay clip ngay",
    "Quay video và lưu",
    "Ghi lại video ngay",
]:
    add(uid("video_capture"), G_MC, query, "ACTION_VIDEO_CAPTURE", {}, False)

# ============================================================
# 20. open_settings  (12 samples)
# ============================================================
G_SF = "settings_files"
_settings: list[tuple[str, str]] = [
    ("Mở cài đặt Wi-Fi", "wifi"),
    ("Vào phần cài đặt Bluetooth", "bluetooth"),
    ("Mở cài đặt chung", "general"),
    ("Bật chế độ máy bay trong cài đặt", "airplane_mode"),
    ("Mở cài đặt vị trí", "location"),
    ("Vào cài đặt màn hình", "display"),
    ("Mở cài đặt bảo mật", "security"),
    ("Cho tôi vào cài đặt ngày giờ", "date"),
    ("Cài đặt Wi-Fi cho tôi", "wifi"),
    ("Mở phần cài đặt Bluetooth", "bluetooth"),
    ("Tắt hoặc bật wifi, mở cài đặt mạng không dây", "wifi"),
    ("Vào cài đặt bộ nhớ trong", "internal_storage"),
]
for query, setting_type in _settings:
    add(uid("settings"), G_SF, query, "open_settings", {"setting_type": setting_type}, False)

# ============================================================
# 21. ACTION_GET_CONTENT  (6 samples)
# ============================================================
_gc: list[tuple[str, str, bool]] = [
    ("Chọn một ảnh trong máy", "image/*", False),
    ("Chọn nhiều ảnh", "image/*", True),
    ("Chọn một video từ bộ nhớ", "video/*", False),
    ("Chọn một file âm thanh", "audio/*", False),
    ("Chọn một tài liệu PDF", "application/pdf", False),
    ("Chọn nhiều tệp hình ảnh để dùng", "image/*", True),
]
for query, mime, multiple in _gc:
    add(uid("get_content"), G_SF, query, "ACTION_GET_CONTENT", {"mime_type": mime, "allow_multiple": multiple}, False)

# ============================================================
# 22. ACTION_OPEN_DOCUMENT  (6 samples)
# ============================================================
_od: list[tuple[str, list[str], bool]] = [
    ("Mở tệp PDF", ["application/pdf"], False),
    ("Mở nhiều tệp PDF", ["application/pdf"], True),
    ("Mở tài liệu Word", ["application/msword"], False),
    ("Mở nhiều tài liệu để dùng lâu dài", ["application/pdf", "application/msword"], True),
    ("Mở file văn bản", ["text/plain"], False),
    ("Mở nhiều ảnh để xem lâu dài", ["image/*"], True),
]
for query, mime_types, multiple in _od:
    add(uid("open_doc"), G_SF, query, "ACTION_OPEN_DOCUMENT", {"mime_types": mime_types, "allow_multiple": multiple}, False)

# ============================================================
# 23. ACTION_CREATE_DOCUMENT  (6 samples)
# ============================================================
_cd: list[tuple[str, str, str]] = [
    ("Tạo tệp văn bản mới tên ghi_chu.txt", "text/plain", "ghi_chu.txt"),
    ("Tạo file PDF mới tên bao_cao.pdf", "application/pdf", "bao_cao.pdf"),
    ("Tạo tài liệu mới tên ke_hoach.txt", "text/plain", "ke_hoach.txt"),
    ("Tạo file văn bản tên nhat_ky.txt", "text/plain", "nhat_ky.txt"),
    ("Tạo tệp mới tên cong_viec.txt kiểu văn bản", "text/plain", "cong_viec.txt"),
    ("Tạo tài liệu text tên to_do.txt", "text/plain", "to_do.txt"),
]
for query, mime, name in _cd:
    add(uid("create_doc"), G_SF, query, "ACTION_CREATE_DOCUMENT", {"mime_type": mime, "initial_name": name}, False)

# ============================================================
# 24. ACTION_GET_RINGTONE  (3 samples)
# ============================================================
for query in [
    "Mở bộ chọn nhạc chuông",
    "Cho tôi chọn nhạc chuông",
    "Đổi nhạc chuông điện thoại",
]:
    add(uid("ringtone"), G_SF, query, "ACTION_GET_RINGTONE", {}, False)

# ============================================================
# 25. Negative / Ambiguous  (60 samples)
# ============================================================
G_NA = "negative_ambiguous"

_unsupported = [
    # Original 15
    "Đặt một chiếc pizza hải sản giao tới nhà tôi",
    "Chuyển khoản 200 nghìn cho bạn Nam qua ngân hàng",
    "Đặt xe Grab về nhà",
    "Tìm hiểu giá cổ phiếu hôm nay",
    "Đăng bài lên Facebook",
    "Mở ứng dụng ngân hàng Vietcombank",
    "Dịch câu này sang tiếng Anh",
    "Đọc tin tức cho tôi nghe",
    "Phát nhạc bài Shape of You",
    "Tắt điện thoại",
    "Khởi động lại máy",
    "Gọi taxi cho tôi",
    "Đặt vé máy bay Hà Nội đi Đà Nẵng",
    "Đặt phòng khách sạn cho 2 người",
    "Mua hàng trên Shopee",
    # New 15 — thêm mẫu unsupported
    "Đặt đồ ăn trưa giao tới công ty",
    "Thanh toán hóa đơn tiền điện qua ứng dụng",
    "Tra cứu số dư tài khoản ngân hàng",
    "Đặt vé tàu từ Sài Gòn ra Hà Nội",
    "Đăng ảnh lên Instagram",
    "Chơi game Liên Quân",
    "Chỉnh sửa ảnh chân dung xóa phông nền",
    "Tạo file Word báo cáo doanh thu",
    "Đăng trạng thái lên Zalo",
    "Chuyển tiền cho mẹ qua tài khoản",
    "Đặt vé xem phim rạp CGV",
    "Gọi đồ ăn từ GrabFood",
    "Tạo bài thuyết trình PowerPoint",
    "Xem giá vàng hôm nay",
    "Đặt bàn ăn tối tại nhà hàng",
]
for query in _unsupported:
    add(uid("unsupported"), G_NA, query, None, {}, False, "unsupported")

_clarification = [
    # Original 15
    "Đặt báo thức cho tôi",
    "Gọi điện cho mẹ tôi",
    "Nhắn tin cho bạn tôi",
    "Gửi email cho sếp",
    "Tìm đường đến đó",
    "Thêm sự kiện vào lịch",
    "Lưu số này vào danh bạ",
    "Mở nó lên",
    "Tìm cái đó trên bản đồ",
    "Tạo tệp mới",
    "Hẹn giờ",
    "Gửi thông tin này",
    "Gọi lại",
    "Tìm trong danh bạ",
    "Chụp cái đó",
    # New 15 — thêm mẫu clarification
    "Gọi cho bạn tôi",
    "Nhắn tin đến đó",
    "Gửi email cho họ",
    "Chụp ảnh và gửi đi",
    "Tạo sự kiện quan trọng",
    "Đặt báo thức",
    "Tìm đường đi",
    "Gọi điện về nhà",
    "Soạn tin nhắn mới",
    "Gửi thông báo cho mọi người",
    "Mở file đó lên",
    "Lưu thông tin này vào danh bạ",
    "Tạo nhắc nhở mới",
    "Chia sẻ cái này cho bạn",
    "Gửi địa chỉ đó qua tin nhắn",
]
for query in _clarification:
    add(uid("clarification"), G_NA, query, None, {}, False, "clarification")

# ============================================================
# Write output
# ============================================================
OUT = Path(__file__).resolve().parents[1] / "data" / "eval" / "vi_droidcall_v1.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8") as f:
    for row in SAMPLES:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

# Summary
groups = Counter(s["group"] for s in SAMPLES)
tools = Counter(s["expected"]["tool"] for s in SAMPLES)

print(f"Wrote {len(SAMPLES)} samples to {OUT}")
print("\nBy group:")
for g, n in sorted(groups.items()):
    print(f"  {g}: {n}")
print(f"\nBy tool (top 10):")
for t, n in tools.most_common(10):
    print(f"  {t}: {n}")
print(f"\nUnique tools covered: {len(tools) - (1 if None in tools else 0)} / 24")
print(f"Null-tool samples: {tools.get(None, 0)}")
