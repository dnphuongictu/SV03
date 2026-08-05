"""Create aug4 targeted augmentation for v7 training.

Targets 4 error categories found in v6 external144 analysis:
  A. Negative-unsupported (plausible but unsupported tools: screenshot, video_call, install_app, dark_mode, play_music, view_calendar)
  B. SMS send_message without subject field (stop adding subject="")
  C. web_search without engine field (stop adding engine="google")
  D. Contact tool disambiguation (get_contact_info vs VIEW vs EDIT vs INSERT)
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from common import ROOT, load_jsonl, write_jsonl
from validate import ToolValidator

OUT_PATH = ROOT / "data" / "eval" / "vi_droidcall_targeted_aug4_v7.jsonl"
EXTERNAL_PATH = ROOT / "data" / "eval" / "vi_droidcall_external_test.jsonl"
TRAIN329_PATH = ROOT / "data" / "eval" / "vi_droidcall_train329_v6_external_robust.jsonl"


def _e(tool, args, confirm, status=None):
    row = {"tool": tool, "arguments": args, "requires_confirmation": confirm}
    if status is not None:
        row["status"] = status
    return row


def _norm(text):
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


# ── Group A: negatives that look like a real tool but are unsupported ──────────
# Pattern: screenshot, video_call, install_app, dark_mode, play_music,
#          view_calendar, call_back_missed, manage_storage
_GROUP_A = [
    ("aug4_neg_001",
     "Chụp màn hình cho tôi",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_002",
     "Bắt đầu quay video màn hình",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_003",
     "Gọi video cho anh Hùng",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_004",
     "Tôi muốn FaceTime với em",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_005",
     "Bật chế độ tối ngay",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_006",
     "Chuyển sang dark mode",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_007",
     "Tải và cài Zalo về máy",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_008",
     "Cài đặt Chrome từ CH Play",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_009",
     "Mở nhạc lên nghe",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_010",
     "Phát bài hát yêu thích của tôi",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_011",
     "Xem lịch ngày mai",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_012",
     "Hiển thị lịch tháng này",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_013",
     "Gọi lại số vừa gọi nhỡ",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_014",
     "Dọn dẹp bộ nhớ trong",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_015",
     "Xóa file rác trong máy",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
    ("aug4_neg_016",
     "Quản lý ứng dụng đang chạy",
     _e(None, {}, False, "unsupported"),
     "neg_unsupported"),
]

# ── Group B: SMS send_message WITHOUT subject ──────────────────────────────────
_GROUP_B = [
    ("aug4_sms_001",
     "Nhắn tin cho 0912345678: anh ơi cho em xin tài liệu",
     _e("send_message", {"phone_number": "0912345678",
                         "body": "anh ơi cho em xin tài liệu"}, True),
     "sms_no_subject"),
    ("aug4_sms_002",
     "Soạn tin nhắn tới 0934 567 890: Em đang bận họp",
     _e("send_message", {"phone_number": "0934567890",
                         "body": "Em đang bận họp"}, True),
     "sms_no_subject"),
    ("aug4_sms_003",
     "Gửi SMS đến 0978 111 222 nội dung: OK sẽ đến đúng giờ",
     _e("send_message", {"phone_number": "0978111222",
                         "body": "OK sẽ đến đúng giờ"}, True),
     "sms_no_subject"),
    ("aug4_sms_004",
     "Nhắn tin 0965432100: xong rồi anh nhé",
     _e("send_message", {"phone_number": "0965432100",
                         "body": "xong rồi anh nhé"}, True),
     "sms_no_subject"),
    ("aug4_sms_005",
     "Gửi tin nhắn cho số 0987 654 321: Cho tôi hỏi còn phòng không",
     _e("send_message", {"phone_number": "0987654321",
                         "body": "Cho tôi hỏi còn phòng không"}, True),
     "sms_no_subject"),
    ("aug4_sms_006",
     "Nhắn cho 0941 000 999: đến nơi rồi đợi mình tí",
     _e("send_message", {"phone_number": "0941000999",
                         "body": "đến nơi rồi đợi mình tí"}, True),
     "sms_no_subject"),
]

# ── Group C: web_search WITHOUT engine ────────────────────────────────────────
_GROUP_C = [
    ("aug4_web_001",
     "Tìm kiếm thời tiết Hà Nội ngày mai",
     _e("web_search", {"query": "thời tiết Hà Nội ngày mai"}, False),
     "web_no_engine"),
    ("aug4_web_002",
     "Search công thức làm bánh flan",
     _e("web_search", {"query": "công thức làm bánh flan"}, False),
     "web_no_engine"),
    ("aug4_web_003",
     "Tìm thông tin về vaccine COVID mới nhất",
     _e("web_search", {"query": "vaccine COVID mới nhất"}, False),
     "web_no_engine"),
    ("aug4_web_004",
     "Search học bổng du học Nhật Bản 2026",
     _e("web_search", {"query": "học bổng du học Nhật Bản 2026"}, False),
     "web_no_engine"),
    # WITH explicit engine — contrast examples
    ("aug4_web_005",
     "Tìm kết quả bóng đá trên Google",
     _e("web_search", {"query": "kết quả bóng đá", "engine": "google"}, False),
     "web_with_engine"),
    ("aug4_web_006",
     "Search trên Google: giá vé máy bay Hà Nội đi Đà Nẵng",
     _e("web_search", {"query": "giá vé máy bay Hà Nội đi Đà Nẵng",
                       "engine": "google"}, False),
     "web_with_engine"),
]

# ── Group D: Contact tool disambiguation ──────────────────────────────────────
# get_contact_info: lấy một trường cụ thể (email, phone, address, birthday)
# ACTION_VIEW_CONTACT: xem toàn bộ thông tin contact theo URI
# ACTION_EDIT_CONTACT: sửa thông tin contact
# ACTION_INSERT_CONTACT: tạo contact mới
_GROUP_D = [
    ("aug4_contact_001",
     "Lấy địa chỉ email của Minh trong danh bạ",
     _e("get_contact_info", {"name": "Minh", "key": "email"}, False),
     "contact_get_field"),
    ("aug4_contact_002",
     "Cho tôi biết số điện thoại của chị Lan",
     _e("get_contact_info", {"name": "Lan", "key": "phone"}, False),
     "contact_get_field"),
    ("aug4_contact_003",
     "Lấy địa chỉ nhà của anh Tuấn trong danh bạ",
     _e("get_contact_info", {"name": "Tuấn", "key": "address"}, False),
     "contact_get_field"),
    ("aug4_contact_004",
     "Mở thông tin liên hệ của Hương để xem",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "Hương"}, False),
     "contact_view"),
    ("aug4_contact_005",
     "Hiển thị trang chi tiết contact của anh Đức",
     _e("ACTION_VIEW_CONTACT", {"contact_uri": "Đức"}, False),
     "contact_view"),
    ("aug4_contact_006",
     "Sửa số điện thoại của chị Mai trong danh bạ",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "Mai"}, True),
     "contact_edit"),
    ("aug4_contact_007",
     "Cập nhật email của anh Quân",
     _e("ACTION_EDIT_CONTACT", {"contact_uri": "Quân"}, True),
     "contact_edit"),
    ("aug4_contact_008",
     "Thêm liên hệ mới: Nguyễn Văn Bình, số 0912 888 777",
     _e("ACTION_INSERT_CONTACT",
        {"contact_info": {"name": "Nguyễn Văn Bình", "phone": "0912888777"}}, True),
     "contact_insert"),
    ("aug4_contact_009",
     "Lưu số mới: Trần Thị Cúc, 0966 234 567",
     _e("ACTION_INSERT_CONTACT",
        {"contact_info": {"name": "Trần Thị Cúc", "phone": "0966234567"}}, True),
     "contact_insert"),
]

ALL_ROWS = (
    [(id_, q, exp, grp) for id_, q, exp, grp in _GROUP_A]
    + [(id_, q, exp, grp) for id_, q, exp, grp in _GROUP_B]
    + [(id_, q, exp, grp) for id_, q, exp, grp in _GROUP_C]
    + [(id_, q, exp, grp) for id_, q, exp, grp in _GROUP_D]
)

EXPECTED_COUNT = 16 + 6 + 6 + 9  # = 37


def main():
    validator = ToolValidator(ROOT / "data" / "tools" / "android_tools.json")
    external = {_norm(r["query"]) for r in load_jsonl(EXTERNAL_PATH)}
    train329 = {_norm(r["query"]) for r in load_jsonl(TRAIN329_PATH)}
    blocked  = external | train329

    seen_ids = set()
    records = []

    for id_, query, expected, group in ALL_ROWS:
        assert id_ not in seen_ids, f"Duplicate ID: {id_}"
        seen_ids.add(id_)

        nq = _norm(query)
        assert nq not in blocked, f"Overlap with locked data: {id_} — {query}"

        status = expected.get("status")
        if status:
            assert status in ("unsupported", "clarification"), \
                f"Invalid status '{status}' in {id_}"

        if expected.get("tool"):
            errors = validator.validate(expected)
            assert not errors, f"Schema error in {id_}: {errors}"

        records.append({
            "id": id_,
            "query": query,
            "expected": expected,
            "group": group,
        })

    assert len(records) == EXPECTED_COUNT, f"Expected {EXPECTED_COUNT} got {len(records)}"

    groups = {}
    for r in records:
        groups.setdefault(r["group"], 0)
        groups[r["group"]] += 1

    print(f"aug4 samples: {len(records)}")
    for g, n in sorted(groups.items()):
        print(f"  {g}: {n}")

    write_jsonl(OUT_PATH, records)
    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    main()
