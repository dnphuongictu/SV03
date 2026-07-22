"""
Kiểm tra 30 benchmark queries (on-device) có overlap với training data không.
Dùng character trigram Jaccard similarity (cùng logic với DATASET_AUDIT).

Usage:
    python src/check_benchmark_overlap.py
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "eval"

# ── 30 benchmark queries (từ BenchmarkReceiver.kt / benchmark_ondevice.py) ──
BENCHMARK = [
    # alarm_calendar (0-4)
    ("bm00", "Đặt báo thức 7 giờ sáng mai",                  "ACTION_SET_ALARM"),
    ("bm01", "Hẹn giờ 10 phút",                               "ACTION_SET_TIMER"),
    ("bm02", "Đặt báo thức lúc 6 giờ với nhãn tập gym",      "ACTION_SET_ALARM"),
    ("bm03", "Hẹn giờ 5 phút để pha trà",                    "ACTION_SET_TIMER"),
    ("bm04", "Thêm lịch họp nhóm lúc 2 giờ chiều mai",       "ACTION_INSERT_EVENT"),
    # contact_call (5-9)
    ("bm05", "Gọi cho anh Minh",                              "dial"),
    ("bm06", "Gọi cho số 0912345678",                         "dial"),
    ("bm07", "Gọi cho số 0901234567",                         "dial"),
    ("bm08", "Tìm thông tin liên hệ của chị Lan",            "get_contact_info"),
    ("bm09", "Thêm liên hệ mới tên Tuấn số 0911234567",      "ACTION_INSERT_CONTACT"),
    # map_web_camera (10-14)
    ("bm10", "Tìm cà phê gần đây",                           "search_location"),
    ("bm11", "Tìm kiếm thời tiết hôm nay",                   "web_search"),
    ("bm12", "Chỉ đường đến Bệnh viện Chợ Rẫy",              "search_location"),
    ("bm13", "Chụp ảnh ngay bây giờ",                        "ACTION_IMAGE_CAPTURE"),
    ("bm14", "Tìm trên Google giá vé máy bay Hà Nội Đà Nẵng","web_search"),
    # message_email (15-19)
    ("bm15", "Nhắn tin cho 0987654321: Tôi đến rồi",         "send_message"),
    ("bm16", "Nhắn tin 0912345678: Tôi đang trên đường",     "send_message"),
    ("bm17", "Gửi email cho an@example.com tiêu đề Báo cáo", "send_email"),
    ("bm18", "Soạn email cho boss@company.com chủ đề Nghỉ phép","send_email"),
    ("bm19", "Nhắn tin cho anh Nam: Nhớ mang tài liệu",      "send_message"),
    # settings_files (20-24)
    ("bm20", "Mở cài đặt WiFi",                              "open_settings"),
    ("bm21", "Mở cài đặt Bluetooth",                         "open_settings"),
    ("bm22", "Chọn một ảnh từ thư viện",                     "ACTION_GET_CONTENT"),
    ("bm23", "Soạn văn bản mới tên bien_ban_hop.docx",         "ACTION_CREATE_DOCUMENT"),
    ("bm24", "Mở tệp PDF trong máy",                         "ACTION_OPEN_DOCUMENT"),
    # negative_ambiguous (25-29)
    ("bm25", "Làm cái này đi",                               None),
    ("bm26", "Gọi cho tôi",                                  None),
    ("bm27", "Đặt pizza hải sản giao đến nhà tôi",           None),
    ("bm28", "Chuyển tiền cho bạn tôi",                      None),
    ("bm29", "Xử lý việc đó hộ tôi",                         None),
]

# ── Training files to check against ──────────────────────────────────────────
TRAIN_FILES = {
    "train191":  DATA / "vi_droidcall_train191_final.jsonl",
    "train299":  DATA / "vi_droidcall_v1.jsonl",
    "train408":  DATA / "vi_droidcall_train408_v8.jsonl",
}

# ── Similarity ────────────────────────────────────────────────────────────────
import unicodedata, re

def normalize(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    nfd  = unicodedata.normalize("NFD", text)
    s    = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.lower().strip())

def trigrams(text: str) -> set[str]:
    t = normalize(text)
    return {t[i:i+3] for i in range(len(t)-2)} if len(t) >= 3 else {t}

def char_sim(a: str, b: str) -> float:
    ta, tb = trigrams(a), trigrams(b)
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)

def exact_match(a: str, b: str) -> bool:
    return normalize(a) == normalize(b)

# ── Load training data ────────────────────────────────────────────────────────
def load_queries(path: Path) -> list[tuple[str, str]]:
    rows = []
    for line in path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        q = rec.get("query", rec.get("input", ""))
        t = (rec.get("expected") or {}).get("tool") or rec.get("tool", "")
        rows.append((q, str(t)))
    return rows

# ── Main ──────────────────────────────────────────────────────────────────────
THRESHOLD = 0.6   # trigram Jaccard ≥ 0.6 = cảnh báo
EXACT_ONLY = False

print("=" * 80)
print("Benchmark query overlap check (30 on-device queries vs training sets)")
print(f"Similarity threshold: {THRESHOLD} (trigram Jaccard)")
print("=" * 80)

all_hits: dict[str, list] = {}   # bm_id → list of (train_file, sim, train_query)

for fname, fpath in TRAIN_FILES.items():
    if not fpath.exists():
        print(f"[SKIP] {fname}: file not found ({fpath.name})")
        continue
    train = load_queries(fpath)
    print(f"\n── {fname} ({len(train)} samples) ──")
    hits = []
    for bm_id, bm_q, bm_tool in BENCHMARK:
        best_sim = 0.0
        best_train = ""
        best_tool  = ""
        for tq, tt in train:
            sim = char_sim(bm_q, tq)
            if sim > best_sim:
                best_sim  = sim
                best_train = tq
                best_tool  = tt
        if best_sim >= THRESHOLD:
            hits.append((bm_id, bm_q, bm_tool, best_sim, best_train, best_tool))
            mark = "EXACT" if exact_match(bm_q, best_train) else f"SIM={best_sim:.3f}"
            print(f"  [{bm_id}] {mark}")
            print(f"    BM : {bm_q}")
            print(f"    TR : {best_train}  (tool={best_tool})")
        all_hits.setdefault(bm_id, [])
        if best_sim >= THRESHOLD:
            all_hits[bm_id].append((fname, best_sim, best_train))
    if not hits:
        print("  (no hits above threshold)")

# ── Cross-file summary ────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("Summary — benchmark queries with ANY similarity ≥ 0.6 to training data")
print("=" * 80)

flagged = [(bm_id, bm_q, bm_tool) for bm_id, bm_q, bm_tool in BENCHMARK
           if all_hits.get(bm_id)]

if not flagged:
    print("CLEAN — no benchmark query exceeds threshold in any training set.")
else:
    print(f"FLAGGED: {len(flagged)}/30 queries have similarity ≥ {THRESHOLD}")
    for bm_id, bm_q, bm_tool in flagged:
        hits_info = all_hits[bm_id]
        max_sim = max(h[1] for h in hits_info)
        print(f"  [{bm_id}]  max_sim={max_sim:.3f}  expected={bm_tool}")
        print(f"    Query : {bm_q}")
        for fname, sim, tq in hits_info:
            print(f"    {fname:12}  sim={sim:.3f}  train: {tq}")

print(f"\nTotal benchmark queries: 30")
print(f"Flagged (sim ≥ {THRESHOLD}): {len(flagged)}")
print(f"Clean: {30 - len(flagged)}")
