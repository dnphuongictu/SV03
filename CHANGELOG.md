# Changelog

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/),
dự án dùng [Semantic Versioning](https://semver.org/lang/vi/).

## [Unreleased]

### Added — 2026-08-05 (chuẩn bị push GitHub: Git LFS cho model)
- `.gitattributes`: theo dõi `*.gguf`, `*.safetensors`, `*.zip` qua Git LFS —
  2 file `.gguf` (469MB, 380MB) vượt giới hạn cứng 100MB/file của GitHub,
  push bằng git thường chắc chắn bị từ chối nếu không có LFS.
- README: hướng dẫn `git lfs install` + cảnh báo quota LFS miễn phí của
  GitHub (1GB lưu trữ/băng thông mỗi tháng) rất sát với ~850MB model đang
  theo dõi — vài lượt clone là có thể vượt.
- **Giấy phép tài sản nền đã được giảng viên xác nhận (Apache-2.0)** cùng
  ngày — cả 2 điều kiện để push public (kỹ thuật + pháp lý) nay đã đủ, xem
  `THIRD_PARTY_NOTICES.md`.

### Cleanup — 2026-08-05 (làm sạch workspace trước khi bàn giao)
- Thêm `.gitignore` (Python cache, Node, Android/Gradle build, IDE, OS junk,
  và `.claude/` — công cụ AI hỗ trợ phiên làm việc, không phải nội dung dự án).
- Xoá `__pycache__/` đã sinh ra trong `src/`, `tests/`.
- Xoá `reports/from_mobile_agent_paper/fresh_locked_repro/results/PAPER_RESULT_SNIPPET.md`
  (đoạn văn bản dự thảo cho bài báo ICTA2026 — không đưa nội dung bài báo đã
  nộp vào repo sinh viên) và sửa các chỗ liệt kê nhắc tới file này trong
  `README.md`/`README_REPRODUCIBILITY.md`/`MANIFEST.json` cùng thư mục cho
  khớp lại.

### Added — 2026-08-05 (bàn giao workspace cho sinh viên)
- `docs/06_BAN_GIAO_SINH_VIEN.md`: tài liệu bàn giao — mục tiêu dự án, bản đồ
  toàn bộ workspace (tài liệu/mã nguồn/dữ liệu/model/báo cáo nền/hạ tầng tuân
  thủ), trạng thái hiện tại, và việc cần làm tiếp theo thứ tự ưu tiên. README
  trỏ tới file này làm điểm khởi đầu khi nhận bàn giao.

### Changed — 2026-08-05 (vòng 2: bảng màu ấm + bỏ emoji, sau phản hồi "vẫn xấu")
- `demo/android_mockup_nguoi_lon_tuoi/`: đổi bảng màu từ xanh dương lạnh sang
  cam ấm (gradient san hô → cam đậm), thêm banner gradient bo góc dưới chứa
  tên app + tagline, thẻ nội dung nằm đè lên mép banner để tạo cảm giác lớp
  thay vì trống trải. Bỏ toàn bộ emoji (🎤✅⏳↩️🤔❌), thay bằng icon micro tự
  vẽ từ hình khối cơ bản (`ic_mic_glyph.xml`), badge tròn màu thương hiệu với
  ký tự đơn sắc, và `ProgressBar` thật cho trạng thái đang xử lý. Đã build,
  cài, chạy thử lại trên điện thoại thật — không crash.

### Changed — 2026-08-05 (làm lại giao diện Android theo Material Design 3)
- `demo/android_mockup_nguoi_lon_tuoi/`: thiết kế lại toàn bộ giao diện theo
  M3 (`Theme.Material3.Light.NoActionBar`, màu theo vai trò M3, `MaterialCardView`
  bo góc có đổ bóng, tiêu đề app ở đầu màn hình) sau phản hồi giao diện bản
  đầu "xấu, độ tương phản không tốt". Sửa một lỗi tương phản thật trong bản
  đầu: nút xác nhận/huỷ có chữ cùng màu với nền (gần như vô hình), nay dùng
  nền đặc (filled) + chữ trắng. Đã build lại, cài và chạy thử trên **điện
  thoại thật** (Samsung Galaxy Note20 5G qua USB, không chỉ máy ảo) — không
  crash, đã xin quyền micro qua đúng hộp thoại hệ thống Android và vào được
  trạng thái nghe thật. Ảnh chụp cập nhật trong
  `demo/android_mockup_nguoi_lon_tuoi/screenshots/`.

### Added — 2026-08-05 (build thử app Android thật)
- `demo/android_mockup_nguoi_lon_tuoi/`: app Android thật (Kotlin, không
  Compose) của mockup người lớn tuổi — dùng `SpeechRecognizer` +
  `TextToSpeech` thật của Android thay vì mô phỏng bằng nút bấm. Đã build
  bằng Gradle 8.10.2/AGP 8.6.0 (`BUILD SUCCESSFUL`), cài và chạy thử trên máy
  ảo Android (Pixel 8, API 37) — không crash, có ảnh chụp màn hình thật trong
  `demo/android_mockup_nguoi_lon_tuoi/screenshots/`. APK debug kèm sẵn tại
  `demo/android_mockup_nguoi_lon_tuoi/releases/`.
- Sửa `skin.path` lỗi thời (trỏ về SDK cũ trên ổ C đã bị xoá) trong AVD
  `Pixel_8` của máy giảng viên — không phải thay đổi trong repo này, ghi chú
  lại để tránh trùng lỗi lần sau.

### Added — 2026-08-05 (định vị ứng dụng: người lớn tuổi)
- Định vị "tính ứng dụng" của dự án: trợ lý giọng nói tối giản thao tác cho
  người lớn tuổi (giọng nói + vài nút to, xác nhận lại lệnh rủi ro trước khi
  thực thi) — chi tiết tại `docs/05_KE_HOACH_DU_THI_PMMN2026.md` mục 3.
- `demo/mockup_nguoi_lon_tuoi.html`: mockup UX tương tác minh hoạ 3 tình
  huống (lệnh an toàn tự thực hiện, lệnh rủi ro cần xác nhận bằng 2 nút to,
  lệnh thiếu thông tin cần hỏi lại) — dùng để trình chiếu, không phải công cụ
  gán nhãn.
- `docs/03_SO_TAY_DU_LIEU.md`: bổ sung hướng dẫn viết câu theo văn phong
  người lớn tuổi thật (câu dài, vòng vo, từ đệm, gọi sai thuật ngữ ứng dụng)
  và bảng gán `risk_level` theo mức hậu quả nếu xác nhận sai.

### Added — 2026-08-05 (bổ sung tài sản nền để bàn giao cho sinh viên)
- `models/from_mobile_agent_paper/adapter_v8/`: adapter LoRA đúng phiên bản
  tạo ra kết quả headline Fresh126 (trước đó repo chỉ có `adapter_v4_final`,
  một phiên bản cũ hơn — dễ gây nhầm lẫn khi tái lập số liệu).
- `reports/from_mobile_agent_paper/`: kết quả benchmark gốc dạng file thô
  (main_report.json, predictions từng câu, script/notebook đánh giá, bằng
  chứng so sánh baseline hybrid vs BM25, benchmark on-device, báo cáo
  Pilot22) — xem chỉ mục và các lưu ý về độ chắc chắn/loại trừ trong
  `reports/from_mobile_agent_paper/README.md`.

### Cần làm trước khi phát hành `v0.1.0`
- Giảng viên hướng dẫn xác nhận giấy phép cho tài sản nền
  `source_code/from_mobile_agent_paper` (xem `THIRD_PARTY_NOTICES.md`).
- Nhóm hoàn thành 500 câu dữ liệu đã kiểm tra, hai người gán nhãn độc lập
  (xem `docs/00_HUONG_DAN_GIANG_VIEN_VA_SINH_VIEN.md`, lộ trình 8 tuần).
- Xác nhận đã nộp phiếu đăng ký dự thi PMMN 2026 cho DT03 (xem
  `docs/05_KE_HOACH_DU_THI_PMMN2026.md` mục 0).

## [0.1.0-dev] - 2026-08-05

### Added
- `LICENSE` (Apache-2.0) cho phần mã nguồn/tài liệu do nhóm sinh viên tự viết.
- `THIRD_PARTY_NOTICES.md`: liệt kê giấy phép các model/dataset/công cụ tham
  khảo (Qwen2.5, llama.cpp, DroidCall) và cảnh báo rủi ro giấy phép của tài
  sản nền `from_mobile_agent_paper`.
- `docs/04_KET_QUA_NGHIEN_CUU_NEN.md`: tổng hợp kết quả thực nghiệm mới nhất
  từ dự án nghiên cứu gốc (ToolAcc, E2E, kết quả on-device thật, kết luận đã
  kiểm định thống kê) để nhóm dùng làm điểm neo khi báo cáo.
- `docs/05_KE_HOACH_DU_THI_PMMN2026.md`: kế hoạch dự thi PMMN 2026, đối chiếu
  từng tiêu chí chấm điểm với hiện trạng và việc cần làm.
- `demo/`: công cụ web gán nhãn dữ liệu ViDroidCall (form nhập câu lệnh, dựng
  đối số theo intent, kiểm tra lỗi ngay khi nhập, dashboard phân bố
  intent/split/risk, xuất/nhập JSONL) — chạy tĩnh bằng
  `python -m http.server 8000 -d demo`, không cần cài thêm gói.
- `demo/validate.js`: cổng JavaScript của logic kiểm định trong
  `src/vidroid_validator.py`, có test `node --test` để tránh hai bản logic
  (Python CLI và web tool) lệch nhau.
- Hướng dẫn cài đặt/build từ mã nguồn đầy đủ hơn trong `README.md`.

### Known limitations
- Dataset hiện tại (`data/sample_vidroidcall.jsonl`) chỉ có 6 câu mẫu minh
  họa, chưa đạt mục tiêu tối thiểu 500 câu của đề cương.
- Chưa có GitHub Release/tag phiên bản.
