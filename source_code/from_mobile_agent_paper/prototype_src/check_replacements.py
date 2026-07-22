"""Verify replacement queries không trùng training data."""
import json, sys, io, unicodedata, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "eval"

def normalize(text):
    text = text.replace("đ","d").replace("Đ","D")
    nfd = unicodedata.normalize("NFD", text)
    s = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.lower().strip())

def trigrams(text):
    t = normalize(text)
    return {t[i:i+3] for i in range(len(t)-2)} if len(t) >= 3 else {t}

def sim(a, b):
    ta, tb = trigrams(a), trigrams(b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 1.0

candidates = [
    ("bm23_new", "Soạn văn bản mới tên bien_ban_hop.docx", "ACTION_CREATE_DOCUMENT"),
    ("bm29_new", "Xử lý việc đó hộ tôi", None),
]

files = [
    "vi_droidcall_train191_final.jsonl",
    "vi_droidcall_v1.jsonl",
    "vi_droidcall_train408_v8.jsonl",
]

for fname in files:
    path = DATA / fname
    train = [json.loads(l)["query"] for l in path.read_text("utf-8").splitlines() if l.strip()]
    for cid, cq, _ in candidates:
        best = max(train, key=lambda tq: sim(cq, tq))
        s = sim(cq, best)
        flag = " ⚠️ TOO CLOSE" if s >= 0.6 else " ✓"
        print(f"{cid}  {fname[:30]}  max_sim={s:.3f}  match={best}{flag}")
