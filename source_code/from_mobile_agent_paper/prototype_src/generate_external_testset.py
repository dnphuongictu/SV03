"""
Generate external test set vi_droidcall_external_test.jsonl
~140 queries covering all 24 Android Intent types + 20 negative examples.

Designed to be DIFFERENT from training data:
- Different names, phone numbers, locations
- Different Vietnamese phrasings and sentence structures
- Mix of formal and colloquial tone
- Some borderline/ambiguous cases included in negative group

Usage:
    python src/generate_external_testset.py [--output data/eval/vi_droidcall_external_test.jsonl]
"""
import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from common import ROOT

OUTPUT_DEFAULT = ROOT / "data" / "eval" / "vi_droidcall_external_test.jsonl"


def _e(tool, args, confirm):
    return {"tool": tool, "arguments": args, "requires_confirmation": confirm}


def _neg():
    return {"tool": None, "arguments": {}, "requires_confirmation": False}


NEGATIVE_STATUSES = {
    "neg_001": "clarification",
    "neg_002": "clarification",
    "neg_003": "clarification",
    "neg_004": "clarification",
    "neg_005": "unsupported",
    "neg_006": "unsupported",
    "neg_007": "clarification",
    "neg_008": "clarification",
    "neg_009": "unsupported",
    "neg_010": "unsupported",
    "neg_011": "unsupported",
    "neg_012": "unsupported",
    "neg_013": "unsupported",
    "neg_014": "unsupported",
    "neg_015": "unsupported",
    "neg_016": "unsupported",
    "neg_017": "clarification",
    "neg_018": "clarification",
    "neg_019": "unsupported",
    "neg_020": "unsupported",
}


# ---------------------------------------------------------------------------
# DATA — each entry: (id_suffix, query, expected, group)
# ---------------------------------------------------------------------------
RAW = [

    # =========================================================================
    # GROUP: alarm_calendar
    # =========================================================================

    # ACTION_SET_ALARM
    ("alarm_001", "Cài báo thức lúc 6 giờ rưỡi sáng giúp tôi",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 6, "EXTRA_MINUTES": 30}, False), "alarm_calendar"),

    ("alarm_002", "Đặt chuông lúc 7 giờ 45 phút nhắc họp sáng",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 7, "EXTRA_MINUTES": 45, "EXTRA_MESSAGE": "họp sáng"}, False), "alarm_calendar"),

    ("alarm_003", "Cần báo thức 5 giờ sáng thứ Hai và thứ Tư mỗi tuần",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 5, "EXTRA_MINUTES": 0, "EXTRA_DAYS": ["Monday", "Wednesday"]}, False), "alarm_calendar"),

    ("alarm_004", "Hẹn chuông 23 giờ 30 để nhắc uống thuốc",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 23, "EXTRA_MINUTES": 30, "EXTRA_MESSAGE": "uống thuốc"}, False), "alarm_calendar"),

    ("alarm_005", "Báo thức mỗi thứ Bảy và Chủ Nhật lúc 8 giờ sáng",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 8, "EXTRA_MINUTES": 0, "EXTRA_DAYS": ["Saturday", "Sunday"]}, False), "alarm_calendar"),

    ("alarm_006", "Đặt alarm lúc 22 giờ kém 15 để nhắc tắt máy tính",
     _e("ACTION_SET_ALARM", {"EXTRA_HOUR": 21, "EXTRA_MINUTES": 45, "EXTRA_MESSAGE": "tắt máy tính"}, False), "alarm_calendar"),

    # ACTION_SET_TIMER
    ("timer_001", "Đặt đồng hồ đếm ngược 20 phút",
     _e("ACTION_SET_TIMER", {"duration": "20 minutes"}, False), "alarm_calendar"),

    ("timer_002", "Hẹn giờ 1 tiếng rưỡi cho nồi cơm",
     _e("ACTION_SET_TIMER", {"duration": "1 hour 30 minutes", "EXTRA_MESSAGE": "nồi cơm"}, False), "alarm_calendar"),

    ("timer_003", "Tôi cần đếm ngược 45 giây",
     _e("ACTION_SET_TIMER", {"duration": "45 seconds"}, False), "alarm_calendar"),

    ("timer_004", "Bật timer 2 tiếng để ôn bài",
     _e("ACTION_SET_TIMER", {"duration": "2 hours", "EXTRA_MESSAGE": "ôn bài"}, False), "alarm_calendar"),

    ("timer_005", "Bật đồng hồ đếm 30 phút nha",
     _e("ACTION_SET_TIMER", {"duration": "30 minutes"}, False), "alarm_calendar"),

    # ACTION_SHOW_ALARMS
    ("showalarm_001", "Liệt kê tất cả báo thức đang có trên máy",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),

    ("showalarm_002", "Kiểm tra các alarm tôi đã cài",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),

    ("showalarm_003", "Mở màn hình quản lý chuông báo",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),

    ("showalarm_004", "Xem lại các báo thức đang bật",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),

    ("showalarm_005", "Có báo thức nào đang hoạt động không, cho tôi xem",
     _e("ACTION_SHOW_ALARMS", {}, False), "alarm_calendar"),

    # ACTION_INSERT_EVENT
    ("event_001", "Thêm lịch họp nhóm vào thứ Sáu lúc 3 giờ chiều tại phòng B2",
     _e("ACTION_INSERT_EVENT", {"TITLE": "họp nhóm", "DESCRIPTION": "cuộc họp nhóm", "EVENT_LOCATION": "phòng B2", "EXTRA_EVENT_BEGIN_TIME": "Friday 15:00"}, True), "alarm_calendar"),

    ("event_002", "Tạo sự kiện sinh nhật chị Thảo vào ngày 15 tháng 8",
     _e("ACTION_INSERT_EVENT", {"TITLE": "sinh nhật chị Thảo", "DESCRIPTION": "sinh nhật chị Thảo", "EXTRA_EVENT_BEGIN_TIME": "2026-08-15"}, True), "alarm_calendar"),

    ("event_003", "Đặt lịch khám nha khoa 9 giờ sáng ngày 20 tháng 6",
     _e("ACTION_INSERT_EVENT", {"TITLE": "khám nha khoa", "DESCRIPTION": "hẹn khám nha khoa", "EXTRA_EVENT_BEGIN_TIME": "2026-06-20 09:00"}, True), "alarm_calendar"),

    ("event_004", "Thêm reminder bảo vệ đồ án ngày mai 8h30 ở hội trường A",
     _e("ACTION_INSERT_EVENT", {"TITLE": "bảo vệ đồ án", "DESCRIPTION": "bảo vệ đồ án", "EVENT_LOCATION": "hội trường A", "EXTRA_EVENT_BEGIN_TIME": "tomorrow 08:30"}, True), "alarm_calendar"),

    ("event_005", "Tạo lịch chạy bộ sáng thứ Hai và thứ Tư lúc 6 giờ",
     _e("ACTION_INSERT_EVENT", {"TITLE": "chạy bộ sáng", "DESCRIPTION": "lịch tập chạy bộ buổi sáng", "EXTRA_EVENT_BEGIN_TIME": "Monday 06:00"}, True), "alarm_calendar"),

    # =========================================================================
    # GROUP: contact_call
    # =========================================================================

    # dial
    ("dial_001", "Gọi điện cho anh Bảo theo số 0912 345 678",
     _e("dial", {"phone_number": "0912345678"}, True), "contact_call"),

    ("dial_002", "Bấm số 0936 222 111 gọi cho chị Phúc",
     _e("dial", {"phone_number": "0936222111"}, True), "contact_call"),

    ("dial_003", "Gọi đến số tổng đài 1800 1234",
     _e("dial", {"phone_number": "18001234"}, True), "contact_call"),

    ("dial_004", "Quay số 028 3823 4567 cho cửa hàng",
     _e("dial", {"phone_number": "02838234567"}, True), "contact_call"),

    ("dial_005", "Mở trình quay số với 0977 001 002",
     _e("dial", {"phone_number": "0977001002"}, True), "contact_call"),

    # get_contact_info
    ("getcontact_001", "Cho tôi số điện thoại của anh Quân",
     _e("get_contact_info", {"name": "Quân", "key": "phone"}, False), "contact_call"),

    ("getcontact_002", "Email của chị Linh là gì?",
     _e("get_contact_info", {"name": "Linh", "key": "email"}, False), "contact_call"),

    ("getcontact_003", "Tìm địa chỉ nhà bác Hùng giúp tôi",
     _e("get_contact_info", {"name": "Hùng", "key": "address"}, False), "contact_call"),

    ("getcontact_004", "Lấy URI liên hệ của em Đức",
     _e("get_contact_info", {"name": "Đức", "key": "uri"}, False), "contact_call"),

    ("getcontact_005", "Số điện thoại của khách hàng Nguyễn Thị Hương là bao nhiêu?",
     _e("get_contact_info", {"name": "Nguyễn Thị Hương", "key": "phone"}, False), "contact_call"),

    # get_contact_info_from_uri
    ("geturi_001", "Từ URI contacts://123 lấy địa chỉ email",
     _e("get_contact_info_from_uri", {"contact_uri": "contacts://123", "key": "email"}, False), "contact_call"),

    ("geturi_002", "Dùng URI content://contacts/people/45 tra số điện thoại",
     _e("get_contact_info_from_uri", {"contact_uri": "content://contacts/people/45", "key": "phone"}, False), "contact_call"),

    ("geturi_003", "Lấy địa chỉ nhà từ URI liên hệ content://contacts/5",
     _e("get_contact_info_from_uri", {"contact_uri": "content://contacts/5", "key": "address"}, False), "contact_call"),

    ("geturi_004", "Tìm email của contact URI content://com.android.contacts/contacts/88",
     _e("get_contact_info_from_uri", {"contact_uri": "content://com.android.contacts/contacts/88", "key": "email"}, False), "contact_call"),

    ("geturi_005", "URI contacts://id/16 — lấy số điện thoại",
     _e("get_contact_info_from_uri", {"contact_uri": "contacts://id/16", "key": "phone"}, False), "contact_call"),

    # ACTION_INSERT_CONTACT
    ("inscontact_001", "Thêm liên hệ mới: Trần Văn Phúc, số 0901 234 567",
     _e("ACTION_INSERT_CONTACT", {"contact_info": {"name": "Trần Văn Phúc", "phone": "0901234567"}}, True), "contact_call"),

    ("inscontact_002", "Lưu danh bạ cho Lê Thị Bảo, email lethibao@gmail.com",
     _e("ACTION_INSERT_CONTACT", {"contact_info": {"name": "Lê Thị Bảo", "email": "lethibao@gmail.com"}}, True), "contact_call"),

    ("inscontact_003", "Tạo contact mới tên Nguyễn Đức Quân, công ty ABC Corp",
     _e("ACTION_INSERT_CONTACT", {"contact_info": {"name": "Nguyễn Đức Quân", "company": "ABC Corp"}}, True), "contact_call"),

    ("inscontact_004", "Thêm số của Thảo Linh 0888 777 666 vào danh bạ",
     _e("ACTION_INSERT_CONTACT", {"contact_info": {"name": "Thảo Linh", "phone": "0888777666"}}, True), "contact_call"),

    ("inscontact_005", "Lưu contact: Phạm Hữu Dũng, điện thoại 0965 111 222, địa chỉ 15 Lý Thường Kiệt",
     _e("ACTION_INSERT_CONTACT", {"contact_info": {"name": "Phạm Hữu Dũng", "phone": "0965111222", "address": "15 Lý Thường Kiệt"}}, True), "contact_call"),

    # ACTION_EDIT_CONTACT
    ("editcontact_001", "Sửa thông tin liên hệ có URI contacts://id/33",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "contacts://id/33"}, True), "contact_call"),

    ("editcontact_002", "Cập nhật danh bạ với URI content://contacts/people/12",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "content://contacts/people/12"}, True), "contact_call"),

    ("editcontact_003", "Chỉnh sửa liên hệ contacts://123 cho tôi",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "contacts://123"}, True), "contact_call"),

    ("editcontact_004", "Mở form sửa contact content://com.android.contacts/contacts/7",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "content://com.android.contacts/contacts/7"}, True), "contact_call"),

    ("editcontact_005", "Tôi muốn cập nhật contact URI contacts://data/55",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "contacts://data/55"}, True), "contact_call"),

    # ACTION_VIEW_CONTACT
    ("viewcontact_001", "Xem thông tin liên hệ contacts://id/10",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "contacts://id/10"}, False), "contact_call"),

    ("viewcontact_002", "Hiển thị chi tiết contact URI content://contacts/people/5",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "content://contacts/people/5"}, False), "contact_call"),

    ("viewcontact_003", "Mở hồ sơ liên hệ content://com.android.contacts/contacts/3",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "content://com.android.contacts/contacts/3"}, False), "contact_call"),

    ("viewcontact_004", "Cho tôi xem profile contact URI contacts://88",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "contacts://88"}, False), "contact_call"),

    ("viewcontact_005", "Tìm và hiển thị thông tin contact content://contacts/data/66",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "content://contacts/data/66"}, False), "contact_call"),

    # ACTION_PICK
    ("pick_001", "Cho tôi chọn một liên hệ từ danh bạ",
     _e("ACTION_PICK", {"data_type": "ALL"}, False), "contact_call"),

    ("pick_002", "Mở danh bạ để tôi chọn số điện thoại",
     _e("ACTION_PICK", {"data_type": "PHONE"}, False), "contact_call"),

    ("pick_003", "Tôi cần chọn địa chỉ email từ danh bạ",
     _e("ACTION_PICK", {"data_type": "EMAIL"}, False), "contact_call"),

    ("pick_004", "Mở bộ chọn địa chỉ liên hệ",
     _e("ACTION_PICK", {"data_type": "ADDRESS"}, False), "contact_call"),

    ("pick_005", "Cho phép tôi chọn một contact bất kỳ",
     _e("ACTION_PICK", {"data_type": "ALL"}, False), "contact_call"),

    # =========================================================================
    # GROUP: map_web_camera
    # =========================================================================

    # search_location
    ("loc_001", "Tìm đường đến trường Đại học Bách Khoa TP.HCM",
     _e("search_location", {"query": "trường Đại học Bách Khoa TP.HCM"}, False), "map_web_camera"),

    ("loc_002", "Mở bản đồ tìm Vincom Center Bà Triệu Hà Nội",
     _e("search_location", {"query": "Vincom Center Bà Triệu Hà Nội"}, False), "map_web_camera"),

    ("loc_003", "Chỉ đường đến bệnh viện Chợ Rẫy",
     _e("search_location", {"query": "bệnh viện Chợ Rẫy"}, False), "map_web_camera"),

    ("loc_004", "Tìm kiếm địa chỉ sân bay Tân Sơn Nhất trên bản đồ",
     _e("search_location", {"query": "sân bay Tân Sơn Nhất"}, False), "map_web_camera"),

    ("loc_005", "Định vị nhà hàng Phở Thìn 13 Lò Đúc Hà Nội",
     _e("search_location", {"query": "Phở Thìn 13 Lò Đúc Hà Nội"}, False), "map_web_camera"),

    # web_search
    ("web_001", "Tìm kiếm thông tin về bão số 3 trên Google",
     _e("web_search", {"query": "bão số 3", "engine": "google"}, False), "map_web_camera"),

    ("web_002", "Search lịch trình bay Hà Nội Đà Nẵng ngày mai",
     _e("web_search", {"query": "lịch trình bay Hà Nội Đà Nẵng ngày mai"}, False), "map_web_camera"),

    ("web_003", "Tra hướng dẫn nấu canh chua cá lóc",
     _e("web_search", {"query": "hướng dẫn nấu canh chua cá lóc"}, False), "map_web_camera"),

    ("web_004", "Tìm kết quả bóng đá hôm nay",
     _e("web_search", {"query": "kết quả bóng đá hôm nay"}, False), "map_web_camera"),

    ("web_005", "Tra cứu giá vé máy bay VietJet tháng 7",
     _e("web_search", {"query": "giá vé máy bay VietJet tháng 7"}, False), "map_web_camera"),

    # ACTION_IMAGE_CAPTURE (capture and return URI immediately)
    ("imgcap_001", "Chụp ảnh nhanh và lưu lại cho tôi",
     _e("ACTION_IMAGE_CAPTURE", {}, False), "map_web_camera"),

    ("imgcap_002", "Bấm chụp một tấm hình ngay bây giờ",
     _e("ACTION_IMAGE_CAPTURE", {}, False), "map_web_camera"),

    ("imgcap_003", "Chụp ảnh và trả về file ảnh",
     _e("ACTION_IMAGE_CAPTURE", {}, False), "map_web_camera"),

    ("imgcap_004", "Tôi cần chụp một cái ảnh và lấy đường dẫn",
     _e("ACTION_IMAGE_CAPTURE", {}, False), "map_web_camera"),

    ("imgcap_005", "Capture ảnh ngay đi",
     _e("ACTION_IMAGE_CAPTURE", {}, False), "map_web_camera"),

    # ACTION_VIDEO_CAPTURE (capture and return URI immediately)
    ("vidcap_001", "Quay video ngay và lưu file lại",
     _e("ACTION_VIDEO_CAPTURE", {}, False), "map_web_camera"),

    ("vidcap_002", "Bấm record video ngay bây giờ",
     _e("ACTION_VIDEO_CAPTURE", {}, False), "map_web_camera"),

    ("vidcap_003", "Ghi hình ngay và lưu URI video",
     _e("ACTION_VIDEO_CAPTURE", {}, False), "map_web_camera"),

    ("vidcap_004", "Quay clip nhanh rồi trả về đường dẫn",
     _e("ACTION_VIDEO_CAPTURE", {}, False), "map_web_camera"),

    ("vidcap_005", "Chụp video và trả kết quả",
     _e("ACTION_VIDEO_CAPTURE", {}, False), "map_web_camera"),

    # INTENT_ACTION_STILL_IMAGE_CAMERA (open camera app, don't capture yet)
    ("camstill_001", "Mở ứng dụng máy ảnh cho tôi",
     _e("INTENT_ACTION_STILL_IMAGE_CAMERA", {}, False), "map_web_camera"),

    ("camstill_002", "Bật camera lên, tôi tự chụp sau",
     _e("INTENT_ACTION_STILL_IMAGE_CAMERA", {}, False), "map_web_camera"),

    ("camstill_003", "Khởi động app chụp hình",
     _e("INTENT_ACTION_STILL_IMAGE_CAMERA", {}, False), "map_web_camera"),

    ("camstill_004", "Mở camera ở chế độ ảnh tĩnh",
     _e("INTENT_ACTION_STILL_IMAGE_CAMERA", {}, False), "map_web_camera"),

    ("camstill_005", "Tôi muốn mở máy ảnh để chụp",
     _e("INTENT_ACTION_STILL_IMAGE_CAMERA", {}, False), "map_web_camera"),

    # INTENT_ACTION_VIDEO_CAMERA (open in video mode, don't record yet)
    ("camvid_001", "Mở camera ở chế độ quay video",
     _e("INTENT_ACTION_VIDEO_CAMERA", {}, False), "map_web_camera"),

    ("camvid_002", "Bật ứng dụng quay phim lên",
     _e("INTENT_ACTION_VIDEO_CAMERA", {}, False), "map_web_camera"),

    ("camvid_003", "Khởi động camera video, tôi tự quay",
     _e("INTENT_ACTION_VIDEO_CAMERA", {}, False), "map_web_camera"),

    ("camvid_004", "Vào ứng dụng camera để quay video",
     _e("INTENT_ACTION_VIDEO_CAMERA", {}, False), "map_web_camera"),

    ("camvid_005", "Mở chế độ quay video trên camera",
     _e("INTENT_ACTION_VIDEO_CAMERA", {}, False), "map_web_camera"),

    # =========================================================================
    # GROUP: message_email
    # =========================================================================

    # send_message
    ("sms_001", "Nhắn tin cho số 0901 234 567: Tôi đang trên đường, 15 phút nữa đến",
     _e("send_message", {"phone_number": "0901234567", "body": "Tôi đang trên đường, 15 phút nữa đến"}, True), "message_email"),

    ("sms_002", "Gửi SMS đến 0912 888 999 nội dung: anh ơi bữa trưa ăn gì",
     _e("send_message", {"phone_number": "0912888999", "body": "anh ơi bữa trưa ăn gì"}, True), "message_email"),

    ("sms_003", "Soạn tin nhắn tới 0966 777 888: Chiều nay họp lúc 3h nhé",
     _e("send_message", {"phone_number": "0966777888", "body": "Chiều nay họp lúc 3h nhé"}, True), "message_email"),

    ("sms_004", "Nhắn 0977 123 456 rằng hàng đã về kho rồi",
     _e("send_message", {"phone_number": "0977123456", "body": "hàng đã về kho rồi"}, True), "message_email"),

    ("sms_005", "Gửi tin nhắn đến 0911 000 111 nội dung: ok anh",
     _e("send_message", {"phone_number": "0911000111", "body": "ok anh"}, True), "message_email"),

    ("sms_006", "Soạn SMS đến 0988 234 567: Nhớ đến đúng giờ nha em",
     _e("send_message", {"phone_number": "0988234567", "body": "Nhớ đến đúng giờ nha em"}, True), "message_email"),

    # send_email
    ("email_001", "Gửi email cho phucnguyen@company.vn tiêu đề Báo cáo tháng 6, nội dung: Gửi anh báo cáo tháng này",
     _e("send_email", {"to": ["phucnguyen@company.vn"], "subject": "Báo cáo tháng 6", "body": "Gửi anh báo cáo tháng này"}, True), "message_email"),

    ("email_002", "Soạn mail đến support@helpdesk.com chủ đề Yêu cầu hỗ trợ kỹ thuật, thân gửi: tôi cần được hỗ trợ",
     _e("send_email", {"to": ["support@helpdesk.com"], "subject": "Yêu cầu hỗ trợ kỹ thuật", "body": "tôi cần được hỗ trợ"}, True), "message_email"),

    ("email_003", "Email cho thao.le@uni.edu.vn và bao.tran@uni.edu.vn về Thông báo lịch thi cuối kỳ",
     _e("send_email", {"to": ["thao.le@uni.edu.vn", "bao.tran@uni.edu.vn"], "subject": "Thông báo lịch thi cuối kỳ", "body": "Thông báo lịch thi cuối kỳ"}, True), "message_email"),

    ("email_004", "Gửi thư điện tử đến boss@corp.com, chủ đề: Xin phép nghỉ phép, nội dung: Tôi xin phép nghỉ 2 ngày",
     _e("send_email", {"to": ["boss@corp.com"], "subject": "Xin phép nghỉ phép", "body": "Tôi xin phép nghỉ 2 ngày"}, True), "message_email"),

    ("email_005", "Compose email đến client@email.com subject: Proposal Q3, body: Kính gửi quý khách",
     _e("send_email", {"to": ["client@email.com"], "subject": "Proposal Q3", "body": "Kính gửi quý khách"}, True), "message_email"),

    ("email_006", "Gửi email nội bộ cho team@company.com, subject Meeting minutes, body: Tóm tắt cuộc họp hôm nay",
     _e("send_email", {"to": ["team@company.com"], "subject": "Meeting minutes", "body": "Tóm tắt cuộc họp hôm nay"}, True), "message_email"),

    # =========================================================================
    # GROUP: settings_files
    # =========================================================================

    # open_settings
    ("settings_001", "Điều hướng đến mục WiFi trong phần cài đặt",
     _e("open_settings", {"setting_type": "wifi"}, False), "settings_files"),

    ("settings_002", "Tìm và mở trang kết nối Bluetooth",
     _e("open_settings", {"setting_type": "bluetooth"}, False), "settings_files"),

    ("settings_003", "Mở màn hình cài đặt vị trí GPS",
     _e("open_settings", {"setting_type": "location"}, False), "settings_files"),

    ("settings_004", "Bật chế độ máy bay giúp tôi",
     _e("open_settings", {"setting_type": "airplane_mode"}, False), "settings_files"),

    ("settings_005", "Vào cài đặt màn hình hiển thị",
     _e("open_settings", {"setting_type": "display"}, False), "settings_files"),

    ("settings_006", "Mở cài đặt bộ nhớ trong",
     _e("open_settings", {"setting_type": "internal_storage"}, False), "settings_files"),

    # ACTION_OPEN_DOCUMENT
    ("opendoc_001", "Mở tài liệu PDF từ bộ nhớ",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["application/pdf"]}, False), "settings_files"),

    ("opendoc_002", "Chọn một file Word để mở",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["application/msword"]}, False), "settings_files"),

    ("opendoc_003", "Tôi cần mở một hình ảnh PNG",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["image/png"]}, False), "settings_files"),

    ("opendoc_004", "Mở file âm thanh MP3",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["audio/mpeg"]}, False), "settings_files"),

    ("opendoc_005", "Chọn và mở nhiều ảnh JPG cùng lúc",
     _e("ACTION_OPEN_DOCUMENT", {"mime_types": ["image/jpeg"], "allow_multiple": True}, False), "settings_files"),

    # ACTION_CREATE_DOCUMENT
    ("createdoc_001", "Tạo tài liệu PDF mới tên là Hợp đồng 2026",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "application/pdf", "initial_name": "Hợp đồng 2026"}, False), "settings_files"),

    ("createdoc_002", "Tạo file text mới tên notes.txt",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "text/plain", "initial_name": "notes.txt"}, False), "settings_files"),

    ("createdoc_003", "Lưu tài liệu Word mới tên Báo cáo tháng 7",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "initial_name": "Báo cáo tháng 7"}, False), "settings_files"),

    ("createdoc_004", "Tạo spreadsheet mới tên KPI_Q3.xlsx",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "initial_name": "KPI_Q3.xlsx"}, False), "settings_files"),

    ("createdoc_005", "Tạo tài liệu HTML mới tên index.html",
     _e("ACTION_CREATE_DOCUMENT", {"mime_type": "text/html", "initial_name": "index.html"}, False), "settings_files"),

    # ACTION_GET_CONTENT
    ("getcontent_001", "Tôi muốn chọn một file video để chia sẻ",
     _e("ACTION_GET_CONTENT", {"mime_type": "video/*"}, False), "settings_files"),

    ("getcontent_002", "Chọn một tài liệu PDF để tải lên",
     _e("ACTION_GET_CONTENT", {"mime_type": "application/pdf"}, False), "settings_files"),

    ("getcontent_003", "Lấy một file ảnh bất kỳ để đính kèm",
     _e("ACTION_GET_CONTENT", {"mime_type": "image/*"}, False), "settings_files"),

    ("getcontent_004", "Chọn nhiều file âm nhạc để import",
     _e("ACTION_GET_CONTENT", {"mime_type": "audio/*", "allow_multiple": True}, False), "settings_files"),

    ("getcontent_005", "Tôi cần chọn một file ZIP",
     _e("ACTION_GET_CONTENT", {"mime_type": "application/zip"}, False), "settings_files"),

    # ACTION_GET_RINGTONE
    ("ringtone_001", "Mở trình chọn âm thanh chuông điện thoại",
     _e("ACTION_GET_RINGTONE", {}, False), "settings_files"),

    ("ringtone_002", "Mở bộ chọn ringtone",
     _e("ACTION_GET_RINGTONE", {}, False), "settings_files"),

    ("ringtone_003", "Tôi muốn đổi nhạc chuông điện thoại",
     _e("ACTION_GET_RINGTONE", {}, False), "settings_files"),

    ("ringtone_004", "Mở danh sách nhạc chuông để chọn",
     _e("ACTION_GET_RINGTONE", {}, False), "settings_files"),

    ("ringtone_005", "Chọn âm thanh chuông cho tôi",
     _e("ACTION_GET_RINGTONE", {}, False), "settings_files"),

    # =========================================================================
    # GROUP: negative_ambiguous
    # =========================================================================

    ("neg_001", "Giúp tôi với",
     _neg(), "negative_ambiguous"),

    ("neg_002", "Gọi điện",
     _neg(), "negative_ambiguous"),

    ("neg_003", "Nhắn tin ngay",
     _neg(), "negative_ambiguous"),

    ("neg_004", "Đặt hẹn cho tôi",
     _neg(), "negative_ambiguous"),

    ("neg_005", "Chơi nhạc đi",
     _neg(), "negative_ambiguous"),

    ("neg_006", "Mở ứng dụng mạng xã hội",
     _neg(), "negative_ambiguous"),

    ("neg_007", "Tìm kiếm",
     _neg(), "negative_ambiguous"),

    ("neg_008", "Gửi cho anh ấy",
     _neg(), "negative_ambiguous"),

    ("neg_009", "Quản lý tài chính cho tôi",
     _neg(), "negative_ambiguous"),

    ("neg_010", "Dọn bộ nhớ điện thoại",
     _neg(), "negative_ambiguous"),

    ("neg_011", "Gọi lại cuộc gọi nhỡ vừa rồi",
     _neg(), "negative_ambiguous"),

    ("neg_012", "Cài đặt ứng dụng Zalo",
     _neg(), "negative_ambiguous"),

    ("neg_013", "Xóa hết ảnh cũ trong máy",
     _neg(), "negative_ambiguous"),

    ("neg_014", "Bật chế độ tối cho điện thoại",
     _neg(), "negative_ambiguous"),

    ("neg_015", "Chụp màn hình ngay",
     _neg(), "negative_ambiguous"),

    ("neg_016", "Tôi muốn gọi video cho chị",
     _neg(), "negative_ambiguous"),

    ("neg_017", "Gửi email",
     _neg(), "negative_ambiguous"),

    ("neg_018", "Tìm số điện thoại",
     _neg(), "negative_ambiguous"),

    ("neg_019", "Xem lịch hôm nay",
     _neg(), "negative_ambiguous"),

    ("neg_020", "Kết nối tai nghe Bluetooth",
     _neg(), "negative_ambiguous"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()

    records = []
    for suffix, query, expected, group in RAW:
        if expected["tool"] is None:
            expected = {**expected, "status": NEGATIVE_STATUSES[suffix]}
        records.append({
            "id": f"ext_{suffix}",
            "query": query,
            "expected": expected,
            "group": group,
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    from collections import Counter
    groups = Counter(r["group"] for r in records)
    tools = Counter(r["expected"]["tool"] for r in records)
    print(f"Generated {len(records)} samples -> {args.output}")
    print("\nGroup distribution:")
    for g, c in sorted(groups.items()):
        print(f"  {g:<25}: {c}")
    print(f"\nUnique tools: {len([t for t in tools if t is not None])}")
    print(f"Negative (null tool): {tools[None]}")


if __name__ == "__main__":
    main()
