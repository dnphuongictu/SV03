"""Benchmark on-device inference của VIntentApp qua ADB.

Đo: TTFT (ms), TPS (tok/s), RAM PSS (MB), Battery current (mA) trên Samsung Galaxy Note20 5G.

Usage:
    python src/benchmark_ondevice.py
    python src/benchmark_ondevice.py --device 192.168.1.92:33031 --model v21 --topk 2 --runs 30

Yêu cầu:
    - ADB connected, app com.vintent.app đã install
    - Model GGUF đã push lên /sdcard/Android/data/com.vintent.app/files/
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

# Fix UnicodeEncodeError on Windows console (cp1252 → utf-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "prototype" / "results"

MODEL_PATHS = {
    "v1":  "/sdcard/Android/data/com.vintent.app/files/vidroidcall_q4km.gguf",    # 0.5B fine-tuned
    "v2":  "/sdcard/Android/data/com.vintent.app/files/vidroidcall_v2_q4km.gguf", # 1.5B fine-tuned
    "v21": "/sdcard/Android/data/com.vintent.app/files/vidroidcall_v21_q4km.gguf",# 1.5B fine-tuned v2.1 (E2E=0.906)
    "v21q3": "/sdcard/Android/data/com.vintent.app/files/vidroidcall_v21_q3km.gguf", # v2.1 Q3_K_M
}

# Benchmark queries — 30 queries, 5 per group, phủ 6 nhóm trong eval set
# (group, query_text, expected_tool)  — None = correct answer is tool=null
# CHÚ Ý: thứ tự phải khớp với BenchmarkReceiver.QUERIES trong Android app
BENCHMARK_QUERIES = [
    # --- alarm_calendar (5) ---
    ("alarm_calendar",    "Đặt báo thức 7 giờ sáng mai",                  "ACTION_SET_ALARM"),
    ("alarm_calendar",    "Hẹn giờ 10 phút",                               "ACTION_SET_TIMER"),
    ("alarm_calendar",    "Đặt báo thức lúc 6 giờ với nhãn tập gym",       "ACTION_SET_ALARM"),
    ("alarm_calendar",    "Hẹn giờ 5 phút để pha trà",                     "ACTION_SET_TIMER"),
    ("alarm_calendar",    "Thêm lịch họp nhóm lúc 2 giờ chiều mai",        "ACTION_INSERT_EVENT"),
    # --- contact_call (5) ---
    ("contact_call",      "Gọi cho anh Minh",                               "dial"),
    ("contact_call",      "Gọi cho số 0912345678",                          "dial"),
    ("contact_call",      "Gọi cho số 0901234567",                          "dial"),
    ("contact_call",      "Tìm thông tin liên hệ của chị Lan",              "get_contact_info"),
    ("contact_call",      "Thêm liên hệ mới tên Tuấn số 0911234567",        "ACTION_INSERT_CONTACT"),
    # --- map_web_camera (5) ---
    ("map_web_camera",    "Tìm cà phê gần đây",                             "search_location"),
    ("map_web_camera",    "Tìm kiếm thời tiết hôm nay",                    "web_search"),
    ("map_web_camera",    "Chỉ đường đến Bệnh viện Chợ Rẫy",               "search_location"),
    ("map_web_camera",    "Chụp ảnh ngay bây giờ",                          "ACTION_IMAGE_CAPTURE"),
    ("map_web_camera",    "Tìm trên Google giá vé máy bay Hà Nội Đà Nẵng", "web_search"),
    # --- message_email (5) ---
    ("message_email",     "Nhắn tin cho 0987654321: Tôi đến rồi",           "send_message"),
    ("message_email",     "Nhắn tin 0912345678: Tôi đang trên đường",       "send_message"),
    ("message_email",     "Gửi email cho an@example.com tiêu đề Báo cáo",   "send_email"),
    ("message_email",     "Soạn email cho boss@company.com chủ đề Nghỉ phép","send_email"),
    ("message_email",     "Nhắn tin cho anh Nam: Nhớ mang tài liệu",        "send_message"),
    # --- settings_files (5) ---
    ("settings_files",    "Mở cài đặt WiFi",                                "open_settings"),
    ("settings_files",    "Mở cài đặt Bluetooth",                           "open_settings"),
    ("settings_files",    "Chọn một ảnh từ thư viện",                       "ACTION_GET_CONTENT"),
    ("settings_files",    "Tạo tệp văn bản mới tên ghi_chu.txt",            "ACTION_CREATE_DOCUMENT"),
    ("settings_files",    "Mở tệp PDF trong máy",                           "ACTION_OPEN_DOCUMENT"),
    # --- negative_ambiguous (5) ---
    ("negative_ambiguous","Làm cái này đi",                                  None),
    ("negative_ambiguous","Gọi cho tôi",                                     None),
    ("negative_ambiguous","Đặt pizza hải sản giao đến nhà tôi",             None),
    ("negative_ambiguous","Chuyển tiền cho bạn tôi",                        None),
    ("negative_ambiguous","Mở nó lên",                                       None),
]


def adb(device: str, *args: str, timeout: int = 120) -> str:
    cmd = ["adb", "-s", device] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                            encoding="utf-8", errors="replace")
    return (result.stdout + result.stderr).strip()


def ensure_connected(device: str) -> bool:
    """Reconnect ADB over WiFi if needed."""
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10).stdout
        if device in out and "device" in out:
            return True
    except Exception:
        pass
    print(f"  [adb] reconnecting to {device}...")
    subprocess.run(["adb", "disconnect", device], capture_output=True, timeout=10)
    time.sleep(1)
    subprocess.run(["adb", "connect", device], capture_output=True, timeout=15)
    time.sleep(2)
    return True


def clear_logcat(device: str) -> None:
    ensure_connected(device)
    try:
        adb(device, "logcat", "-c", timeout=15)
    except subprocess.TimeoutExpired:
        print("  [warn] logcat -c timeout, skipping clear")
    time.sleep(0.5)


def read_logcat_until(device: str, tag: str, marker: str, timeout: int = 120) -> list[str]:
    """Đọc logcat cho đến khi gặp marker hoặc timeout."""
    cmd = ["adb", "-s", device, "logcat", "-s", f"{tag}:I", "-T", "1"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True, encoding="utf-8", errors="replace")
    lines = []
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            lines.append(line.strip())
            if marker in line:
                break
    finally:
        proc.terminate()
    return lines


def send_benchmark(device: str, query_id: int, run_id: int, warmup: bool = False,
                   model_path: str | None = None, top_k: int | None = None) -> None:
    warmup_str = "true" if warmup else "false"
    cmd = ["shell", "am", "start",
           "-n", "com.vintent.app/.MainActivity",
           "--ei", "run_id", str(run_id),
           "--ei", "query_id", str(query_id),
           "--ez", "warmup", warmup_str]
    if model_path:
        cmd += ["--es", "model_path", model_path]
    if top_k is not None:
        cmd += ["--ei", "top_k", str(top_k)]
    adb(device, *cmd)


def parse_result(lines: list[str], run_id: int, expected_tool: str | None = ...) -> dict | None:
    result = {}
    for line in lines:
        m = re.search(rf"BENCH_RESULT run={run_id} ttft_ms=(\d+) tps=([\d.]+) tool=(\S+) ok=(true|false)", line)
        if m:
            result["ttft_ms"]      = int(m.group(1))
            result["tps"]          = float(m.group(2))
            result["tool"]         = m.group(3) if m.group(3) != "null" else None
            # Recompute ok based on expected_tool label (handles negative cases)
            if expected_tool is ...:
                result["ok"] = m.group(4) == "true"
            elif expected_tool is None:
                result["ok"] = result["tool"] is None  # negative: correct if null
            else:
                result["ok"] = result["tool"] == expected_tool
        m2 = re.search(rf"BENCH_RAM run={run_id} used_mb=(\d+)", line)
        if m2:
            result["ram_mb"] = int(m2.group(1))
    return result if "ttft_ms" in result else None


def get_pss_ram(device: str) -> int:
    """Lấy PSS RAM (MB) từ dumpsys meminfo — chính xác hơn Runtime.getRuntime()."""
    out = adb(device, "shell", "dumpsys", "meminfo", "com.vintent.app", timeout=10)
    m = re.search(r"TOTAL PSS:\s+(\d+)", out)
    if m:
        return int(m.group(1)) // 1024  # KB → MB
    m2 = re.search(r"TOTAL\s+(\d+)", out)
    return int(m2.group(1)) // 1024 if m2 else 0


def get_battery_current_ma(device: str) -> int:
    """Đọc dòng điện pin hiện tại (mA) từ sysfs — dương = đang xả, âm = đang sạc.
    Samsung Note20 5G: current_now trả về mA trực tiếp (không phải µA).
    Nếu |value| > 10000 thì đổi đơn vị µA → mA."""
    paths = [
        "/sys/class/power_supply/battery/current_now",
        "/sys/class/power_supply/Battery/current_now",
    ]
    for p in paths:
        out = adb(device, "shell", f"cat {p} 2>/dev/null", timeout=5)
        out = out.strip()
        if out and out.lstrip("-").isdigit():
            val = int(out)
            # Nếu |val| > 10000 → µA, cần ÷1000; otherwise là mA
            return val // 1000 if abs(val) > 10000 else val
    # fallback: dumpsys battery (giá trị tính bằng mA)
    out = adb(device, "shell", "dumpsys", "battery", timeout=5)
    m = re.search(r"current now:\s*(-?\d+)", out)
    return int(m.group(1)) if m else 0


def launch_app(device: str) -> None:
    """Mở app lên foreground — benchmark chạy qua onNewIntent trong MainActivity."""
    adb(device, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(1)
    adb(device, "shell", "wm", "dismiss-keyguard")
    adb(device, "shell", "am", "start", "-n", "com.vintent.app/.MainActivity")
    time.sleep(4)  # Chờ activity fully visible và FLAG_KEEP_SCREEN_ON active


def run_benchmark(device: str, n_runs: int, warmup_runs: int,
                  model_path: str, top_k: int = 5) -> dict:
    if "v21" in model_path:
        model_tag = "v2.1(1.5B)"
    elif "v2" in model_path:
        model_tag = "v2(1.5B)"
    else:
        model_tag = "v1(0.5B)"
    print(f"\n{'='*60}")
    print(f"VIntentAgent On-Device Benchmark")
    print(f"Device : {device}")
    print(f"Model  : {model_tag}  {model_path.split('/')[-1]}")
    print(f"topK   : {top_k}")
    print(f"Warmup : {warmup_runs} runs  |  Measured: {n_runs} runs")
    print(f"{'='*60}\n")

    print("[Setup] Launching app to foreground...")
    launch_app(device)

    all_results = []
    run_id = 0

    # Warmup — load/switch model + stabilize thermal
    print(f"[Warmup] {warmup_runs} run(s)...")
    for i in range(warmup_runs):
        qid = i % len(BENCHMARK_QUERIES)
        run_id += 1
        clear_logcat(device)
        # Pass model_path và top_k trên warmup đầu → trigger switch trong app
        mp = model_path if i == 0 else None
        tk = top_k      if i == 0 else None
        send_benchmark(device, qid, run_id, warmup=True, model_path=mp, top_k=tk)
        timeout = 300 if i == 0 else 180
        lines = read_logcat_until(device, "VINTENT_BENCH", f"BENCH_RAM run={run_id}", timeout=timeout)
        r = parse_result(lines, run_id)
        if r:
            print(f"  warmup {i+1}: TTFT={r['ttft_ms']}ms TPS={r['tps']:.1f} RAM={r.get('ram_mb',0)}MB")
        else:
            print(f"  warmup {i+1}: timeout / no result")
        time.sleep(2)

    print()

    # Measured runs
    for idx, (group, query, expected_tool) in enumerate(BENCHMARK_QUERIES[:n_runs]):
        run_id += 1
        print(f"[{run_id-warmup_runs:2d}/{n_runs}] {group:20s} | {query[:40]}")
        clear_logcat(device)
        send_benchmark(device, idx, run_id, warmup=False)
        lines = read_logcat_until(device, "VINTENT_BENCH", f"BENCH_RAM run={run_id}", timeout=180)
        r = parse_result(lines, run_id, expected_tool=expected_tool)
        if r:
            pss     = get_pss_ram(device)
            batt_ma = get_battery_current_ma(device)
            r["pss_mb"]        = pss
            r["battery_ma"]    = batt_ma
            r["group"]         = group
            r["query"]         = query
            r["expected_tool"] = expected_tool
            r["run_id"]        = run_id
            all_results.append(r)
            ok_mark = "✓" if r["ok"] else "✗"
            print(f"         TTFT={r['ttft_ms']:5d}ms  TPS={r['tps']:4.1f}  RAM={pss}MB  "
                  f"Batt={batt_ma}mA  tool={r['tool']}  {ok_mark}")
        else:
            print(f"         TIMEOUT — no result")
        time.sleep(2)

    return all_results


def summarize(results: list[dict]) -> dict:
    if not results:
        return {}
    ttfts   = [r["ttft_ms"]    for r in results]
    tpss    = [r["tps"]        for r in results]
    rams    = [r["pss_mb"]     for r in results if r.get("pss_mb", 0) > 0]
    batts   = [abs(r["battery_ma"]) for r in results if r.get("battery_ma", 0) != 0]
    ok      = sum(1 for r in results if r["ok"])

    summary = {
        "n": len(results),
        "accuracy": round(ok / len(results), 3),
        "ttft_ms": {
            "mean": round(mean(ttfts)),
            "std":  round(stdev(ttfts)) if len(ttfts) > 1 else 0,
            "min":  min(ttfts),
            "max":  max(ttfts),
        },
        "tps": {
            "mean": round(mean(tpss), 1),
            "std":  round(stdev(tpss), 1) if len(tpss) > 1 else 0,
            "min":  min(tpss),
            "max":  max(tpss),
        },
        "ram_pss_mb": {
            "mean": round(mean(rams)) if rams else 0,
            "max":  max(rams) if rams else 0,
        },
        "battery_ma": {
            "mean": round(mean(batts)) if batts else 0,
            "max":  max(batts) if batts else 0,
        },
        "per_group": {},
    }

    groups = {}
    for r in results:
        g = r.get("group", "other")
        groups.setdefault(g, []).append(r)
    for g, rows in groups.items():
        summary["per_group"][g] = {
            "n": len(rows),
            "ttft_mean_ms": round(mean(r["ttft_ms"] for r in rows)),
            "tps_mean":     round(mean(r["tps"]     for r in rows), 1),
            "ok":           sum(1 for r in rows if r["ok"]),
        }

    return summary


def print_summary(summary: dict) -> None:
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    t = summary.get("ttft_ms", {})
    p = summary.get("tps", {})
    r = summary.get("ram_pss_mb", {})
    print(f"  Queries   : {summary.get('n', 0)}")
    print(f"  Accuracy  : {summary.get('accuracy', 0):.1%}")
    print(f"  TTFT      : {t.get('mean',0)}ms ± {t.get('std',0)}ms  (min={t.get('min',0)} max={t.get('max',0)})")
    print(f"  TPS       : {p.get('mean',0)} ± {p.get('std',0)} tok/s")
    b = summary.get("battery_ma", {})
    print(f"  RAM (PSS) : mean={r.get('mean',0)}MB  peak={r.get('max',0)}MB")
    if b.get("mean", 0):
        print(f"  Battery   : mean={b.get('mean',0)}mA  peak={b.get('max',0)}mA (discharge current)")
    print()
    print(f"  {'Group':<22} {'N':>3} {'TTFT(ms)':>9} {'TPS':>6} {'OK':>4}")
    print(f"  {'-'*50}")
    for g, v in summary.get("per_group", {}).items():
        print(f"  {g:<22} {v['n']:>3} {v['ttft_mean_ms']:>9} {v['tps_mean']:>6} {v['ok']:>4}/{v['n']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device",  default="192.168.1.92:33031")
    ap.add_argument("--runs",    type=int, default=30)
    ap.add_argument("--warmup",  type=int, default=2)
    ap.add_argument("--model",   choices=["v1", "v2", "v21", "v21q3"], default="v2",
                    help="v1=0.5B, v2=1.5B, v21=v2.1 Q4_K_M, v21q3=v2.1 Q3_K_M")
    ap.add_argument("--topk",    type=int, default=5,
                    help="BM25 retriever top-K (default=5, try 3 for shorter prompt/faster TTFT)")
    ap.add_argument("--output",  type=Path, default=None)
    args = ap.parse_args()

    # Verify ADB connection
    out = adb(args.device, "devices")
    if args.device not in out or "device" not in out:
        sys.exit(f"[ERROR] Device {args.device} not connected. Run: adb connect {args.device}")

    model_path = MODEL_PATHS[args.model]
    results = run_benchmark(args.device, args.runs, args.warmup, model_path, top_k=args.topk)
    summary = summarize(results)
    print_summary(summary)

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_tag = args.model
    out_path = args.output or (RESULTS_DIR / f"benchmark_ondevice_{model_tag}_top{args.topk}_{ts}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": ts,
        "device": args.device,
        "model": model_path.split("/")[-1],
        "model_version": model_tag,
        "top_k": args.topk,
        "n_runs": args.runs,
        "warmup_runs": args.warmup,
        "summary": summary,
        "raw": results,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] Results saved: {out_path}")


if __name__ == "__main__":
    main()
