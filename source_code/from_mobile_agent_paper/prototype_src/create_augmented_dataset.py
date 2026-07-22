"""Tạo augmented training dataset cho P6.

Gộp:
  1. Clean training data (vi_droidcall_v1.jsonl) — 344 mẫu
  2. Noisy light + medium (từ noisy_queries.jsonl) — 598 mẫu (299×2)
  3. Code-switching training samples (hard-coded, proper args) — ~40 mẫu

Output:
  prototype/data/train/vi_droidcall_augmented.jsonl     (1+2)
  prototype/data/train/vi_droidcall_augmented_cs.jsonl  (1+2+3)

Usage:
    cd prototype
    python -X utf8 src/create_augmented_dataset.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[1]
TRAIN_DIR  = ROOT / "data" / "train"
EVAL_DIR   = ROOT / "data" / "eval"

CLEAN_PATH  = EVAL_DIR / "vi_droidcall_v1.jsonl"
NOISY_PATH  = EVAL_DIR / "noisy_queries.jsonl"
OUT_NOISY   = TRAIN_DIR / "vi_droidcall_augmented.jsonl"
OUT_CS      = TRAIN_DIR / "vi_droidcall_augmented_cs.jsonl"


# ── Code-switching training samples (manual, proper expected outputs) ──────────
# Đủ arguments để train được, bao gồm các pattern Việt-Anh phổ biến nhất.
CS_TRAIN_SAMPLES: list[dict] = [
    # ── Dial ──
    {"id":"cs_train_dial_01","group":"contact_call",
     "query":"Gọi cho số 0912345678 now",
     "expected":{"tool":"dial","arguments":{"phone_number":"0912345678"},"requires_confirmation":True}},
    {"id":"cs_train_dial_02","group":"contact_call",
     "query":"Please gọi 0987654321 giúp tôi",
     "expected":{"tool":"dial","arguments":{"phone_number":"0987654321"},"requires_confirmation":True}},
    {"id":"cs_train_dial_03","group":"contact_call",
     "query":"Call số 0909123456",
     "expected":{"tool":"dial","arguments":{"phone_number":"0909123456"},"requires_confirmation":True}},
    {"id":"cs_train_dial_04","group":"contact_call",
     "query":"Dial 0911002200 giúp tôi",
     "expected":{"tool":"dial","arguments":{"phone_number":"0911002200"},"requires_confirmation":True}},
    {"id":"cs_train_dial_05","group":"contact_call",
     "query":"Gọi cho anh Minh by phone",
     "expected":{"tool":"dial","arguments":{"phone_number":"Minh"},"requires_confirmation":True}},

    # ── Alarm ──
    {"id":"cs_train_alarm_01","group":"alarm_calendar",
     "query":"Set alarm for 6 giờ sáng với label đi học",
     "expected":{"tool":"ACTION_SET_ALARM","arguments":{"EXTRA_HOUR":6,"EXTRA_MINUTES":0,"EXTRA_MESSAGE":"đi học"},"requires_confirmation":False}},
    {"id":"cs_train_alarm_02","group":"alarm_calendar",
     "query":"Đặt báo thức at 7:30 AM",
     "expected":{"tool":"ACTION_SET_ALARM","arguments":{"EXTRA_HOUR":7,"EXTRA_MINUTES":30},"requires_confirmation":False}},
    {"id":"cs_train_alarm_03","group":"alarm_calendar",
     "query":"Wake me up at 5 giờ sáng ngày mai",
     "expected":{"tool":"ACTION_SET_ALARM","arguments":{"EXTRA_HOUR":5,"EXTRA_MINUTES":0},"requires_confirmation":False}},
    {"id":"cs_train_alarm_04","group":"alarm_calendar",
     "query":"Set timer for 15 minutes để nghỉ giải lao",
     "expected":{"tool":"ACTION_SET_TIMER","arguments":{"duration":"15 minutes","EXTRA_MESSAGE":"nghỉ giải lao"},"requires_confirmation":False}},
    {"id":"cs_train_alarm_05","group":"alarm_calendar",
     "query":"Hẹn giờ 10 minutes rồi báo tôi",
     "expected":{"tool":"ACTION_SET_TIMER","arguments":{"duration":"10 minutes"},"requires_confirmation":False}},

    # ── Settings ──
    {"id":"cs_train_settings_01","group":"settings_files",
     "query":"Open settings Wi-Fi",
     "expected":{"tool":"open_settings","arguments":{"setting_type":"wifi"},"requires_confirmation":False}},
    {"id":"cs_train_settings_02","group":"settings_files",
     "query":"Mở Bluetooth settings",
     "expected":{"tool":"open_settings","arguments":{"setting_type":"bluetooth"},"requires_confirmation":False}},
    {"id":"cs_train_settings_03","group":"settings_files",
     "query":"Open cài đặt display",
     "expected":{"tool":"open_settings","arguments":{"setting_type":"display"},"requires_confirmation":False}},
    {"id":"cs_train_settings_04","group":"settings_files",
     "query":"Mở phần security settings",
     "expected":{"tool":"open_settings","arguments":{"setting_type":"security"},"requires_confirmation":False}},
    {"id":"cs_train_settings_05","group":"settings_files",
     "query":"Turn on Wi-Fi và mở cài đặt",
     "expected":{"tool":"open_settings","arguments":{"setting_type":"wifi"},"requires_confirmation":False}},

    # ── Message ──
    {"id":"cs_train_sms_01","group":"message_email",
     "query":"Send message to 0912345678 nội dung tôi đến muộn",
     "expected":{"tool":"send_message","arguments":{"phone_number":"0912345678","subject":"","body":"tôi đến muộn"},"requires_confirmation":True}},
    {"id":"cs_train_sms_02","group":"message_email",
     "query":"Nhắn 0987654321 rằng I'll be late",
     "expected":{"tool":"send_message","arguments":{"phone_number":"0987654321","subject":"","body":"I'll be late"},"requires_confirmation":True}},
    {"id":"cs_train_sms_03","group":"message_email",
     "query":"Send an SMS to 0909123456 says cảm ơn",
     "expected":{"tool":"send_message","arguments":{"phone_number":"0909123456","subject":"","body":"cảm ơn"},"requires_confirmation":True}},
    {"id":"cs_train_email_01","group":"message_email",
     "query":"Send email to minh@gmail.com với subject Báo cáo",
     "expected":{"tool":"send_email","arguments":{"to":["minh@gmail.com"],"subject":"Báo cáo","body":""},"requires_confirmation":True}},
    {"id":"cs_train_email_02","group":"message_email",
     "query":"Gửi email to an@company.com tiêu đề Meeting",
     "expected":{"tool":"send_email","arguments":{"to":["an@company.com"],"subject":"Meeting","body":""},"requires_confirmation":True}},

    # ── Camera ──
    {"id":"cs_train_camera_01","group":"map_web_camera",
     "query":"Open camera và chụp ảnh",
     "expected":{"tool":"INTENT_ACTION_STILL_IMAGE_CAMERA","arguments":{},"requires_confirmation":False}},
    {"id":"cs_train_camera_02","group":"map_web_camera",
     "query":"Take a photo giúp tôi",
     "expected":{"tool":"INTENT_ACTION_STILL_IMAGE_CAMERA","arguments":{},"requires_confirmation":False}},
    {"id":"cs_train_camera_03","group":"map_web_camera",
     "query":"Record video now",
     "expected":{"tool":"INTENT_ACTION_VIDEO_CAMERA","arguments":{},"requires_confirmation":False}},

    # ── Search/Map ──
    {"id":"cs_train_map_01","group":"map_web_camera",
     "query":"Search location gần đây cho quán cà phê",
     "expected":{"tool":"search_location","arguments":{"query":"quán cà phê gần đây"},"requires_confirmation":False}},
    {"id":"cs_train_map_02","group":"map_web_camera",
     "query":"Find directions to sân bay Nội Bài",
     "expected":{"tool":"search_location","arguments":{"query":"sân bay Nội Bài"},"requires_confirmation":False}},
    {"id":"cs_train_web_01","group":"map_web_camera",
     "query":"Search on Google thời tiết Hà Nội",
     "expected":{"tool":"web_search","arguments":{"query":"thời tiết Hà Nội","engine":"google"},"requires_confirmation":False}},
    {"id":"cs_train_web_02","group":"map_web_camera",
     "query":"Google search giá iPhone 15",
     "expected":{"tool":"web_search","arguments":{"query":"giá iPhone 15","engine":"google"},"requires_confirmation":False}},

    # ── Calendar ──
    {"id":"cs_train_cal_01","group":"alarm_calendar",
     "query":"Add event họp nhóm at 2pm tomorrow",
     "expected":{"tool":"ACTION_INSERT_EVENT","arguments":{"TITLE":"họp nhóm","DESCRIPTION":"họp nhóm","EXTRA_EVENT_BEGIN_TIME":"tomorrow 14:00"},"requires_confirmation":True}},
    {"id":"cs_train_cal_02","group":"alarm_calendar",
     "query":"Schedule meeting lúc 9 giờ sáng thứ hai",
     "expected":{"tool":"ACTION_INSERT_EVENT","arguments":{"TITLE":"meeting","DESCRIPTION":"meeting","EXTRA_EVENT_BEGIN_TIME":"Monday 9:00"},"requires_confirmation":True}},

    # ── Files ──
    {"id":"cs_train_file_01","group":"settings_files",
     "query":"Choose a photo from gallery",
     "expected":{"tool":"ACTION_GET_CONTENT","arguments":{"mime_type":"image/*","allow_multiple":False},"requires_confirmation":False}},
    {"id":"cs_train_file_02","group":"settings_files",
     "query":"Create new file tên report.txt",
     "expected":{"tool":"ACTION_CREATE_DOCUMENT","arguments":{"mime_type":"text/plain","initial_name":"report.txt"},"requires_confirmation":False}},

    # ── Contact ──
    {"id":"cs_train_contact_01","group":"contact_call",
     "query":"Add contact tên John số 0912000111",
     "expected":{"tool":"ACTION_INSERT_CONTACT","arguments":{"contact_info":{"name":"John","phone":"0912000111"}},"requires_confirmation":True}},
    {"id":"cs_train_contact_02","group":"contact_call",
     "query":"Search contact tên Minh",
     "expected":{"tool":"get_contact_info","arguments":{"name":"Minh","key":"phone"},"requires_confirmation":False}},

    # ── Negative ──
    {"id":"cs_train_neg_01","group":"negative_ambiguous",
     "query":"Order pizza giao tới nhà tôi please",
     "expected":{"tool":None,"arguments":{},"requires_confirmation":False,"status":"unsupported"}},
    {"id":"cs_train_neg_02","group":"negative_ambiguous",
     "query":"Book a flight to Hanoi cho tôi",
     "expected":{"tool":None,"arguments":{},"requires_confirmation":False,"status":"unsupported"}},
    {"id":"cs_train_neg_03","group":"negative_ambiguous",
     "query":"Set alarm please",
     "expected":{"tool":None,"arguments":{},"requires_confirmation":False,"status":"clarification"}},
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def to_training_row(sample: dict) -> dict:
    """Chuẩn hoá sang format training."""
    return {
        "id":       sample["id"],
        "group":    sample.get("group", "other"),
        "query":    sample["query"],
        "expected": sample["expected"],
    }


def main() -> None:
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Clean training data ─────────────────────────────────────────────────
    clean = load_jsonl(CLEAN_PATH)
    print(f"Clean training data: {len(clean)} samples")

    # ── 2. Noisy light + medium ────────────────────────────────────────────────
    all_noisy = load_jsonl(NOISY_PATH)
    noisy_lm  = [s for s in all_noisy if s.get("noise_level") in ("light", "medium")]

    # Convert: noisy_query → query, keep expected + group
    noisy_rows = []
    for s in noisy_lm:
        noisy_rows.append({
            "id":       s["id"],
            "group":    s.get("group", "other"),
            "query":    s["noisy_query"],   # use noisy version as input
            "expected": s["expected"],
        })
    print(f"Noisy light+medium:  {len(noisy_rows)} samples  ({len(noisy_lm)} total, heavy excluded)")

    # ── 3. CS training samples ─────────────────────────────────────────────────
    cs_rows = [to_training_row(s) for s in CS_TRAIN_SAMPLES]
    print(f"Code-switch manual:  {len(cs_rows)} samples")

    # ── Write datasets ─────────────────────────────────────────────────────────
    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8",
        )

    # Dataset A: clean + noisy (for ASR robustness adapter)
    aug_rows = clean + noisy_rows
    write_jsonl(OUT_NOISY, aug_rows)
    print(f"\nDataset A (clean+noisy): {len(aug_rows)} samples → {OUT_NOISY}")

    # Dataset B: clean + noisy + CS (for combined adapter)
    aug_cs_rows = clean + noisy_rows + cs_rows
    write_jsonl(OUT_CS, aug_cs_rows)
    print(f"Dataset B (clean+noisy+CS): {len(aug_cs_rows)} samples → {OUT_CS}")

    # ── Group distribution ─────────────────────────────────────────────────────
    from collections import Counter
    for name, rows in [("Dataset A", aug_rows), ("Dataset B", aug_cs_rows)]:
        dist = Counter(r["group"] for r in rows)
        print(f"\n{name} group distribution:")
        for g, c in sorted(dist.items()):
            print(f"  {g:<25} {c}")


if __name__ == "__main__":
    main()
