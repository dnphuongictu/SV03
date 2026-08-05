# Kết quả nền — bổ sung từ dự án nghiên cứu gốc (05/08/2026)

Tài sản nền, sao chép có chọn lọc từ `mobile_agent_paper` và gói tái lập
`VIntentAgent_repro` (nằm ngoài repo này). **Không sửa trực tiếp**, cùng quy
ước với `source_code/from_*`, `data/from_*`, `models/from_*`. Bản tóm tắt diễn
giải các số liệu này bằng tiếng Việt nằm ở
`../../docs/04_KET_QUA_NGHIEN_CUU_NEN.md` — đọc file đó trước, quay lại đây khi
cần trích dẫn số liệu thô hoặc chạy lại script.

## Cấu trúc

- `fresh_locked_repro/`: gói tái lập đầy đủ cho kết quả headline Fresh126 (v8,
  hybrid K=5, α=0.7) — `results/main_report.json` là báo cáo gốc,
  `results/v8_hybrid_k5_predictions.jsonl` là dự đoán từng câu trong 126 câu,
  `MANIFEST.json` có SHA-256 khóa từng file, `scripts/` là các script Python
  dùng để tạo test set khóa và đánh giá, `notebooks/` là notebook Kaggle GPU
  đã chạy thật.
- `fresh_baseline_comparison/`: bằng chứng cho kết luận "hybrid retrieval
  KHÔNG chứng minh được lợi thế trên Fresh126" — `FRESH_BASELINE_RESULTS_20260627.md`
  là bảng so sánh, hai file `*_main_report.json` là kết quả thô của từng cấu
  hình (BM25-only K=5 và zero-shot hybrid K=5).
- `ondevice/`: `BAO_CAO_ONDEVICE_RESULT.md` là báo cáo tường thuật (chú ý: đây
  là báo cáo giai đoạn 10/06/2026, số liệu "eval CPU" E2E=0.906, KHÔNG phải số
  liệu điện thoại thật cuối cùng dùng trong paper). Ba file benchmark JSON là
  các lần đo tốc độ/RAM trên điện thoại Samsung Note20 thật gần khớp nhất với
  số liệu paper trích dẫn (ToolAcc 0.67, TTFT 16.1±3.2s, RAM 1204MB) — xem ghi
  chú "độ chắc chắn" bên dưới.
- `execution_pilot/`: báo cáo Pilot22 (13/22 đúng ở bước resolve intent, hành
  động thật không được thực thi). Chỉ gồm JSON/Markdown; **không copy thư mục
  `evidence/` gốc** (xem mục loại trừ).
- `PAPER_NUMBERS_AUDIT_2026-07-01.md`, `PROJECT_HANDOFF_2026-07-01.md`: hai
  tài liệu gốc dùng để xác nhận các số liệu trên khớp với bản thảo nộp
  ICTA2026 — đây là nguồn đáng tin cậy nhất nếu có nghi ngờ về một con số.

## ⚠️ Ghi chú độ chắc chắn — số liệu on-device

`PROJECT_HANDOFF_2026-07-01.md` xác nhận con số cuối trong paper là "Device30
v2.1 BM25 K=2 Q4_K_M: ToolAcc 0.67, TTFT 16.1 ± 3.2 s, RAM PSS 1204 MB", nhưng
dự án gốc có **nhiều lần chạy benchmark on-device gần giống nhau** (ít nhất 8
file `benchmark_ondevice_v21_top2_*.json`) và không có ghi chú nào chỉ đích
danh file nào là bản "đã sửa sau khi thay overlap" được trích trong paper. Hai
file đã copy (`benchmark_v21_1.5B_top2_candidate_A.json`,
`..._candidate_B_20260626.json`) là hai file khớp gần nhất về mặt số liệu
(TTFT ≈ 16.1s và ≈ 14.4s tương ứng) nhưng **không nên coi là xác nhận 100%
đúng chính xác lần chạy đã trích trong paper** — nếu cần độ chính xác tuyệt
đối cho một công bố mới, phải hỏi lại tác giả gốc.

## Những gì cố tình KHÔNG copy, và vì sao

- **`vidroidcall_v21_q4km.gguf`** (model điện thoại dùng cho paper): đã tìm
  trong toàn bộ `mobile_agent_paper` và các thư mục liên quan trên ổ D nhưng
  **không tìm thấy file này còn tồn tại** (có thể đã bị dọn dẹp dù
  `PROJECT_HANDOFF_2026-07-01.md` ghi "không được xóa"). Chỉ có
  `vidroidcall_v2_q4km.gguf` (940MB, phiên bản so sánh khác) tại
  `D:\temp_model_push\`. Nếu cần chạy lại đúng benchmark on-device, phải yêu
  cầu tác giả gốc tìm/tạo lại file này.
- **Thư mục `evidence/` của Pilot22** (ảnh chụp màn hình điện thoại thật khi
  thực thi 22 tác vụ): không copy vì đây là ảnh giao diện điện thoại cá nhân
  thật (bàn phím gọi, danh bạ, SMS...), thuộc diện "dữ liệu nhận dạng/nhạy cảm"
  mà quy ước bộ nền cấm đưa lên repo (`00_BO_NEN_6_DU_AN.md`, mục 7), dù nội
  dung câu lệnh dùng số điện thoại/email giả (đã kiểm tra: `0900000123`,
  `pilot@example.com`...). Nếu cần minh họa cho demo, hãy chụp ảnh mới bằng dữ
  liệu giả tương tự thay vì dùng ảnh gốc.
- **Bản thảo bài báo** (`paper_icta/`, các file `.docx`/`.pdf`): đây là sản
  phẩm nghiên cứu độc lập, đang trong quá trình phản biện, không phải tài sản
  nền của đề tài sinh viên — giữ nguyên ranh giới đã nêu trong
  `docs/04_KET_QUA_NGHIEN_CUU_NEN.md`.
- **`kaggle_input/*.zip`** của gói repro: bỏ qua vì chỉ là bản đóng gói lại
  đúng những file đã có sẵn dạng rời (data, `android_tools.json`, adapter_v8)
  để tải lên Kaggle — giữ lại sẽ trùng lặp dung lượng không cần thiết.
- Các thư mục checkpoint/optimizer trung gian của nhiều phiên bản adapter
  khác (`adapter_v4_aug299`, `adapter_v9`, `adapter_vrobust`,...) trong
  `prototype/results/`: không copy, giữ đúng nguyên tắc "không copy thư mục
  kết quả trung gian lớn" đã áp dụng cho lần copy đầu (xem
  `../../../00_TONG_HOP_MODELS_CODE_DA_COPY.md`).
