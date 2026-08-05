# Kết quả nghiên cứu nền (VIntentAgent / mobile_agent_paper)

Tài liệu này tổng hợp kết quả thực nghiệm **mới nhất** từ dự án nghiên cứu gốc
`mobile_agent_paper` (nằm ngoài repo sinh viên, tại
`D:\OneDrive - DH Cong nghe thong tin & Truyen Thong\mobile_agent_paper`), nơi
`source_code/from_mobile_agent_paper` và `data/from_mobile_agent_paper` trong dự
án này được trích ra làm tài sản nền. Đây là **kết quả tham chiếu**, không phải
đóng góp của sinh viên — dùng để hiểu baseline đã đạt tới đâu và tránh lặp lại
thí nghiệm đã có kết luận rõ.

Bản nộp bài báo gần nhất liên quan: `ICTA2026_paper_154_with_AI_declaration.pdf`
(16/07/2026), kế thừa bản `VIntentAgent_ICTA2026_anonymous_submission` (01/07/2026)
— không tìm thấy xác nhận đã được chấp nhận (accepted/camera-ready) tính đến thời
điểm cập nhật tài liệu này (05/08/2026).

## 1. Bộ test khóa cứng Fresh126

- File: `data/from_mobile_agent_paper/prototype_data/eval/vi_droidcall_fresh_test_locked_20260626.jsonl`
  (126 dòng, đã có sẵn trong repo này) + ledger SHA-256 đi kèm
  (`..._ledger.csv`).
- Đóng băng ngày 26/06/2026, **trước khi** chạy mô hình v8 — kiểm tra không
  trùng exact, không SequenceMatcher ≥ 0.90, không char-3 Jaccard ≥ 0.70 với
  train/dev. Đây là cơ chế chống rò rỉ dữ liệu (data leakage) mà bộ nền 6 dự án
  yêu cầu ("Cổng 5: chỉ thay một yếu tố khi cải tiến, so sánh công bằng" —
  xem `00_BO_NEN_6_DU_AN.md`).
- Sinh viên nên coi Fresh126 là ví dụ mẫu cho quy trình khóa test set của
  chính dataset mới sẽ tạo, **không** dùng lẫn Fresh126 vào augmentation.

## 2. Kết quả headline (v8, hybrid BM25+dense, K=5, α=0.7)

Train dùng `vi_droidcall_train408_v8.jsonl` (407 dòng, có trong repo), đánh giá
trên Fresh126:

| Metric | Giá trị |
|---|---|
| ToolAcc | 0.746 |
| SchemaValid | 0.921 |
| SoftArgAcc | 0.744 |
| E2E (policy-assisted) | 0.563 (Wilson 95% CI [0.476, 0.647]) |

Phân rã lỗi trên 126 câu: 15 sai tool, 1 schema invalid, 15 sai argument, 24
lỗi unsafe/null.

## 3. Kết luận đã kiểm định thống kê (tránh lặp lại thí nghiệm)

- **Fine-tune LoRA giúp nhiều và có ý nghĩa thống kê**: zero-shot Qwen
  E2E = 0.317 so với fine-tuned v8 E2E = 0.563 (McNemar p = 3.31e-5).
- **Hybrid retrieval KHÔNG chứng minh được lợi thế trên test khóa cứng**:
  BM25-only K=5 đạt E2E = 0.627, cao hơn hybrid (0.563), p = 0.152 (không có
  ý nghĩa). Kết quả ngược chiều với xu hướng +6.2pp nghiêng về hybrid quan sát
  trên dev set (final48/Ext144, N nhỏ, CI chồng lấn) — bài học: **không kết
  luận từ dev set nhỏ, phải xác nhận lại trên test khóa**.
- Không có ablation tách riêng đóng góp của constrained decoding/schema
  validator khỏi phần fine-tune — đây là khoảng trống RQ1 của đề cương
  (`02_DE_CUONG_NCKH_TOI_THIEU.md`) mà nhóm sinh viên có thể tự làm, vì công cụ
  (`vidroid_validator.py`) đã có sẵn trong đề tài này.

## 4. Kết quả on-device thật (Samsung Note20 5G, GGUF Q4_K_M, top-K=2)

| Phiên bản | Kích thước | ToolAcc | TTFT | TPS | RAM (PSS) | Dòng điện |
|---|---|---|---|---|---|---|
| v1 (Qwen2.5-0.5B) | 379 MB | 0.50 | 4.9 ± 1.1 s | 4.8 | 578 MB | ~378 mA |
| v2.1 (Qwen2.5-1.5B, bản dùng cho paper) | 940 MB | 0.67 | 16.1 ± 3.2 s | 1.4 | 1204 MB | ~445 mA TB / 816 mA đỉnh |

Lưu ý: chỉ có Q4_K_M được đo on-device thật; không có so sánh FP16 vs Q8_0 vs
Q4_K_M trên điện thoại thật trong nghiên cứu gốc (chỉ có trên máy tính), nên
**không nên tuyên bố kết luận về ảnh hưởng riêng của quantization từ số liệu
on-device** — đây là hạn chế đã ghi trong paper gốc, không phải điều sinh viên
cần chứng minh lại.

Pilot thực thi thật (Pilot22, 22 câu): chỉ 13/22 đúng ở bước "pre-action Intent
resolution"; hành động nhạy cảm cuối cùng (gọi điện/nhắn tin thật) **không được
thực thi thật trong pilot** — đúng nguyên tắc an toàn của bộ nền ("Không chạy
lệnh gọi/SMS thật" — `00_HUONG_DAN_GIANG_VIEN_VA_SINH_VIEN.md`).

## 5. Khoảng cách giữa repo sinh viên và kết quả nghiên cứu gốc

Cập nhật 05/08/2026: đã bổ sung thêm các mục dưới đây từ dự án gốc, xem chỉ
mục đầy đủ tại `reports/from_mobile_agent_paper/README.md`.

Đã có sẵn trong repo này (không cần xin thêm):

- Bộ test khóa Fresh126 + ledger SHA-256
  (`data/from_mobile_agent_paper/prototype_data/eval/`).
- Dữ liệu train v8 (`vi_droidcall_train408_v8.jsonl`) và các bản train/aug
  trung gian khác trong `data/from_mobile_agent_paper/prototype_data/`.
- Model GGUF Q4_K_M (`qwen2.5-0.5b-instruct-q4_k_m.gguf`,
  `vidroidcall_q4km.gguf`) và **cả hai** adapter LoRA:
  `models/from_mobile_agent_paper/adapter_v4_final` (cũ) và
  `models/from_mobile_agent_paper/adapter_v8` (đúng adapter tạo ra kết quả
  headline ở mục 2 — dùng adapter này nếu cần tái lập ToolAcc 0.746).
- File kết quả benchmark gốc: `reports/from_mobile_agent_paper/fresh_locked_repro/`
  (main_report.json, fresh_analysis.json, dự đoán từng câu, script đánh giá,
  notebook Kaggle đã chạy thật) và
  `reports/from_mobile_agent_paper/fresh_baseline_comparison/` (bằng chứng
  hybrid không thắng BM25-only).
- Số liệu on-device: `reports/from_mobile_agent_paper/ondevice/` (báo cáo +
  2 file benchmark JSON gần khớp nhất với số liệu bảng ở mục 4 — xem ghi chú
  "độ chắc chắn" trong README của thư mục đó, vì dự án gốc có nhiều lần chạy
  gần giống nhau và không đánh dấu rõ lần nào là bản "đã sửa cuối cùng").
- Báo cáo Pilot22 dạng văn bản (không kèm ảnh chụp màn hình thật):
  `reports/from_mobile_agent_paper/execution_pilot/`.

Chưa có và **không tìm thấy** trong dự án gốc (đã tìm trên toàn ổ đĩa, không
chỉ trong `mobile_agent_paper`):

- `vidroidcall_v21_q4km.gguf` — model điện thoại chính xác đã dùng để đo số
  liệu on-device trong paper. File này được ghi trong tài liệu bàn giao gốc là
  "không được xóa" nhưng thực tế không còn tồn tại ở bất kỳ đâu đã kiểm tra.
  Chỉ có `vidroidcall_v2_q4km.gguf` (940MB, phiên bản so sánh khác, không phải
  bản dùng cho paper) tại `D:\temp_model_push\` trên máy giảng viên — nếu cần,
  phải hỏi trực tiếp tác giả gốc.

Cố ý không copy (xem lý do đầy đủ trong
`reports/from_mobile_agent_paper/README.md`):

- Bản thân bài báo (`paper_icta/`) — sản phẩm nghiên cứu độc lập, đang phản
  biện, không phải tài sản nền của đề tài sinh viên.
- Ảnh chụp màn hình thật của Pilot22 (`evidence/`) — ảnh giao diện điện thoại
  cá nhân, thuộc diện dữ liệu nhạy cảm bị cấm theo quy ước bộ nền.

## 6. Áp dụng vào đề tài sinh viên

1. Dùng bảng số liệu ở mục 2 và 4 làm **điểm neo** khi báo cáo: nếu dataset mới
   do nhóm tạo (500+ câu) được đánh giá lại trên cùng adapter/model, kết quả
   nên được so sánh với ToolAcc 0.746 / E2E 0.563 của Fresh126, không so sánh
   với dev set.
2. Vì hybrid retrieval chưa chứng minh được lợi thế, **baseline mặc định nên
   là BM25-only hoặc rule/template** (đúng nguyên tắc "mỗi đề tài phải có
   baseline đơn giản trước AI/LLM" — `00_BO_NEN_6_DU_AN.md`), không mặc định
   chọn hybrid làm baseline.
3. Ghi rõ trong báo cáo: số liệu mục 2–4 là **kết quả nền, không phải do nhóm
   đo lại** — trích dẫn tài liệu này thay vì paper gốc chưa công bố.
