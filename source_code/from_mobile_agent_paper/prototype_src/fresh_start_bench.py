"""Đo TTFT fresh-start cho 1.5B: force-stop app, chờ 10 phút nguội, chạy 1 query."""
from __future__ import annotations
import subprocess, time, re, sys, json
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEVICE     = "192.168.1.46:39295"
MODEL_V2   = "/sdcard/Android/data/com.vintent.app/files/vidroidcall_v2_q4km.gguf"
MODEL_V1   = "/sdcard/Android/data/com.vintent.app/files/vidroidcall_q4km.gguf"
COOLDOWN_S = 600   # 10 phút
RESULTS    = Path(__file__).resolve().parents[1] / "results"

TEST_QUERIES = [
    ("Đặt báo thức 7 giờ sáng mai", "ACTION_SET_ALARM"),
    ("Gọi cho số 0912345678",        "dial"),
    ("Tìm cà phê gần đây",           "search_location"),
]

def adb(*args, timeout=120):
    r = subprocess.run(["adb", "-s", DEVICE] + list(args),
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return (r.stdout + r.stderr).strip()

def read_logcat_until(marker: str, timeout: int = 200) -> list[str]:
    cmd = ["adb", "-s", DEVICE, "logcat", "-s", "VINTENT_BENCH:I,LlamaJNI:I", "-T", "1"]
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

def run_single(model_path: str, query: str, run_id: int) -> dict | None:
    adb("logcat", "-c")
    time.sleep(0.5)
    adb("shell", "am", "start",
        "-n", "com.vintent.app/.MainActivity",
        "--ei", "run_id", str(run_id),
        "--ei", "query_id", "0",      # query_id không dùng — query đến từ QUERIES list
        "--ez", "warmup", "false",
        "--es", "model_path", model_path)
    lines = read_logcat_until(f"BENCH_RAM run={run_id}", timeout=200)
    for line in lines:
        m = re.search(rf"BENCH_RESULT run={run_id} ttft_ms=(\d+) tps=([\d.]+) tool=(\S+)", line)
        if m:
            return {
                "ttft_ms": int(m.group(1)),
                "tps":     float(m.group(2)),
                "tool":    m.group(3) if m.group(3) != "null" else None,
            }
    return None

def main():
    print("=" * 55)
    print("VIntentAgent — Fresh-Start TTFT Benchmark")
    print(f"Device  : {DEVICE}")
    print(f"Cooldown: {COOLDOWN_S // 60} phút")
    print("=" * 55)

    # Force-stop để đảm bảo model unloaded khỏi RAM
    print("\n[1] Force-stopping app...")
    adb("shell", "am", "force-stop", "com.vintent.app")
    time.sleep(2)

    # Cooldown
    print(f"[2] Chờ {COOLDOWN_S // 60} phút để CPU nguội...")
    for remaining in range(COOLDOWN_S, 0, -60):
        print(f"    còn {remaining // 60} phút...")
        time.sleep(60)
    print("    Xong cooldown.")

    # Wake + launch app
    print("\n[3] Waking device and launching app...")
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(1)
    adb("shell", "wm", "dismiss-keyguard")
    adb("shell", "am", "start", "-n", "com.vintent.app/.MainActivity")
    time.sleep(5)   # chờ app load (model chưa load ở bước này)

    results = []

    # --- v2 (1.5B) ---
    print("\n[4] Đo fresh-start 1.5B (v2)...")
    print("    Query: 'Đặt báo thức 7 giờ sáng mai'")
    # Gửi model_path để trigger load 1.5B
    adb("shell", "am", "start",
        "-n", "com.vintent.app/.MainActivity",
        "--ei", "run_id", "1",
        "--ei", "query_id", "0",
        "--ez", "warmup", "false",
        "--es", "model_path", MODEL_V2)
    adb("logcat", "-c"); time.sleep(0.3)
    adb("shell", "am", "start",
        "-n", "com.vintent.app/.MainActivity",
        "--ei", "run_id", "1",
        "--ei", "query_id", "0",
        "--ez", "warmup", "false",
        "--es", "model_path", MODEL_V2)
    lines = read_logcat_until("BENCH_RAM run=1", timeout=200)
    r1 = None
    for line in lines:
        m = re.search(r"BENCH_RESULT run=1 ttft_ms=(\d+) tps=([\d.]+) tool=(\S+)", line)
        if m:
            r1 = {"model": "v2_1.5B", "ttft_ms": int(m.group(1)),
                  "tps": float(m.group(2)), "tool": m.group(3)}
    if r1:
        print(f"    TTFT={r1['ttft_ms']}ms ({r1['ttft_ms']/1000:.1f}s)  TPS={r1['tps']} tok/s  tool={r1['tool']}")
        results.append(r1)
    else:
        print("    TIMEOUT")

    # --- Đợi 5 phút rồi đo v1 (0.5B) để có baseline sạch ---
    print("\n[5] Chờ 5 phút giữa 2 model...")
    for remaining in range(300, 0, -60):
        print(f"    còn {remaining // 60} phút...")
        time.sleep(60)

    # --- v1 (0.5B) ---
    print("\n[6] Đo fresh-start 0.5B (v1)...")
    print("    Query: 'Đặt báo thức 7 giờ sáng mai'")
    adb("shell", "am", "start",
        "-n", "com.vintent.app/.MainActivity",
        "--ei", "run_id", "2",
        "--ei", "query_id", "0",
        "--ez", "warmup", "false",
        "--es", "model_path", MODEL_V1)
    adb("logcat", "-c"); time.sleep(0.3)
    adb("shell", "am", "start",
        "-n", "com.vintent.app/.MainActivity",
        "--ei", "run_id", "2",
        "--ei", "query_id", "0",
        "--ez", "warmup", "false",
        "--es", "model_path", MODEL_V1)
    lines = read_logcat_until("BENCH_RAM run=2", timeout=120)
    r2 = None
    for line in lines:
        m = re.search(r"BENCH_RESULT run=2 ttft_ms=(\d+) tps=([\d.]+) tool=(\S+)", line)
        if m:
            r2 = {"model": "v1_0.5B", "ttft_ms": int(m.group(1)),
                  "tps": float(m.group(2)), "tool": m.group(3)}
    if r2:
        print(f"    TTFT={r2['ttft_ms']}ms ({r2['ttft_ms']/1000:.1f}s)  TPS={r2['tps']} tok/s  tool={r2['tool']}")
        results.append(r2)
    else:
        print("    TIMEOUT")

    # Summary
    print("\n" + "=" * 55)
    print("FRESH-START SUMMARY")
    print("=" * 55)
    for r in results:
        print(f"  {r['model']:12s}  TTFT={r['ttft_ms']:6d}ms ({r['ttft_ms']/1000:.1f}s)  TPS={r['tps']:.1f} tok/s")

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RESULTS / f"fresh_start_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"timestamp": ts, "results": results}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n[OK] Saved: {out}")

if __name__ == "__main__":
    main()
