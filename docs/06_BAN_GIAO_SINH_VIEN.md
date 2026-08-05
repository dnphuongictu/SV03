# Tài liệu bàn giao — ViDroidCall Studio (DT03)

**Đọc file này trước tiên.** Đây là bản đồ toàn bộ workspace: dự án này để
làm gì, đã có sẵn những gì, và nhóm cần làm tiếp những gì. Các tài liệu khác
trong `docs/` đi sâu vào từng phần — file này chỉ dẫn khi nào đọc file nào.

## 0. Tóm tắt một câu

ViDroidCall Studio là công cụ **tạo và kiểm định dữ liệu câu lệnh tiếng Việt**
cho một trợ lý Android chạy **offline**, định vị ứng dụng cho **người lớn
tuổi** (giọng nói + vài nút to + luôn xác nhận lại lệnh rủi ro trước khi làm),
dự thi cuộc thi "Phát triển phần mềm mã nguồn mở tích hợp AI 2026" của
trường.

## 1. Mục tiêu dự án

### 1.1 Bài toán

Phần lớn dữ liệu function-calling cho trợ lý Android (vd DroidCall) là tiếng
Anh. Không có dữ liệu tiếng Việt sạch thì không thể fine-tune một SLM nhỏ để
chạy offline trên điện thoại. ViDroidCall Studio lấp khoảng trống đó: một
schema mở + validator + web tool để tạo, gán nhãn và kiểm tra dữ liệu lệnh
thoại tiếng Việt cho 8 nhóm hành vi Android cơ bản (`set_alarm`, `set_timer`,
`call_contact`, `send_sms`, `open_map`, `open_app`, `unsupported`, `clarify`).

### 1.2 Vì sao chọn "người lớn tuổi" làm câu chuyện ứng dụng

8 intent ở trên vốn đã là đúng bộ lệnh một người lớn tuổi cần: gọi điện, nhắn
tin, xem bản đồ, đặt báo thức — không cần đổi phạm vi dữ liệu. Điểm khác biệt
là **thiết kế tương tác**: giọng nói là chính, tối đa vài nút bấm to, và với
lệnh có thể gây hậu quả khó sửa (gọi nhầm người, nhắn nhầm nội dung) thì **bắt
buộc đọc lại bằng câu tự nhiên và chờ xác nhận** trước khi thực hiện. Lý do
chọn hướng này và cách nó bám vào đúng trường `risk_level` đã có sẵn trong
schema: đọc `docs/05_KE_HOACH_DU_THI_PMMN2026.md` mục 3.

### 1.3 Bối cảnh: đây là một đề tài trong cuộc thi PMMN 2026

- Đội: **DT03 — ViDroidCall Studio** (Đỗ Quang Minh, Lê Quang Hưng, Nguyễn
  Tuấn Anh), là 1 trong 6 đề tài "bộ nền" của Khoa CNTT chuẩn bị cho cuộc thi.
- Repo dự thi: `https://github.com/dnphuongictu/SV03`.
- Mốc thời gian, tiêu chí chấm điểm, và việc cần làm để đạt điểm: xem
  `docs/05_KE_HOACH_DU_THI_PMMN2026.md` — đọc kỹ file này, nó là kim chỉ nam
  cho toàn bộ phần "còn thiếu" ở mục 4 bên dưới.

### 1.4 Việc KHÔNG phải làm

- Không cần fine-tune SLM, không cần tự chạy lại thí nghiệm retrieval/model —
  phần đó đã có kết quả từ dự án nghiên cứu nền, xem mục 2.4.
- Không tự ý coi tài sản trong các thư mục `from_*` là đóng góp của nhóm.
- Không gọi điện/nhắn tin thật, không dùng số điện thoại/danh bạ thật ở bất kỳ
  đâu (dữ liệu, demo, mockup).

## 2. Bản đồ workspace — đã có sẵn những gì

### 2.1 Tài liệu (`docs/`)

| File | Đọc khi nào |
|---|---|
| `00_HUONG_DAN_GIANG_VIEN_VA_SINH_VIEN.md` | Đầu tiên — lộ trình 8 tuần gốc |
| `01_chuan_bi_du_lieu_bai_bao_mo_hinh.md` | Chuẩn bị dữ liệu/model, tài liệu tham khảo |
| `02_DE_CUONG_NCKH_TOI_THIEU.md` | Câu hỏi nghiên cứu RQ1–RQ3 |
| `03_SO_TAY_DU_LIEU.md` | **Bắt buộc đọc trước khi viết bất kỳ câu dữ liệu nào** — quy tắc trường, chống rò rỉ, văn phong người lớn tuổi, cách gán `risk_level` |
| `04_KET_QUA_NGHIEN_CUU_NEN.md` | Số liệu thật đã có (ToolAcc, E2E, on-device) — dùng làm điểm neo khi báo cáo, đừng đo lại từ đầu |
| `05_KE_HOACH_DU_THI_PMMN2026.md` | Kế hoạch dự thi — mốc thời gian, đối chiếu tiêu chí chấm điểm, rủi ro, lộ trình |
| `06_BAN_GIAO_SINH_VIEN.md` | Chính là file này |

### 2.2 Mã nguồn sinh viên (`src/`, `tests/`, `demo/`)

- `src/vidroid_validator.py`: validator CLI chuẩn (Python, standard library).
  Chạy: `python src/vidroid_validator.py data/sample_vidroidcall.jsonl`.
- `tests/test_validator.py`: test Python cho validator.
- `demo/index.html` + `demo/app.js` + `demo/style.css`: **web tool gán nhãn**
  — form nhập câu lệnh, tự dựng field theo intent, validate ngay khi nhập,
  dashboard phân bố, xuất/nhập JSONL. Chạy:
  `python -m http.server 8000 -d demo`.
- `demo/validate.js`: cổng JavaScript của đúng logic trong
  `vidroid_validator.py` (để web tool và CLI không lệch nhau). Test:
  `node --test` (chạy từ gốc repo).
- `demo/mockup_nguoi_lon_tuoi.html`: mockup HTML minh hoạ UX người dùng cuối
  (không phải công cụ gán nhãn) — 3 tình huống bấm chọn được.
- `demo/android_mockup_nguoi_lon_tuoi/`: **app Android thật** của cùng mockup
  (Kotlin, `SpeechRecognizer` + `TextToSpeech` thật, giao diện Material
  Design 3) — đã build và chạy thử thành công trên máy ảo và điện thoại thật
  (Samsung Galaxy Note20 5G). Đây là bản trình diễn UX, KHÔNG dùng SLM/model
  AI thật để nhận intent (chỉ so khớp từ khoá) — xem README riêng trong thư
  mục đó để biết cách build lại và giới hạn của nó.

Cả `demo/mockup_nguoi_lon_tuoi.html` và `demo/android_mockup_nguoi_lon_tuoi/`
là tài sản minh hoạ cho câu chuyện ứng dụng, **không tính là một phần bài tập
bắt buộc** — nhóm có thể dùng để trình diễn, chỉnh sửa, hoặc bỏ qua.

### 2.3 Dữ liệu (`data/`)

- `data/vidroidcall.schema.json`: JSON Schema chính thức.
- `data/sample_vidroidcall.jsonl`: 6 câu mẫu minh hoạ — **chưa đạt** mục tiêu
  500 câu, xem mục 4.
- `data/from_mobile_agent_paper/`: tài sản nền (train/eval JSONL từ dự án
  nghiên cứu gốc, gồm cả **Fresh126** — tập test khoá cứng SHA-256, xem
  `04_KET_QUA_NGHIEN_CUU_NEN.md` mục 1). Không sửa trực tiếp.

### 2.4 Model (`models/`)

- `qwen2.5-0.5b-instruct-q4_k_m.gguf`, `vidroidcall_q4km.gguf`: model GGUF
  nén sẵn.
- `adapter_v4_final/`: adapter LoRA cũ.
- `adapter_v8/`: **adapter đúng** tạo ra kết quả headline ToolAcc 0.746 (xem
  `04_KET_QUA_NGHIEN_CUU_NEN.md`) — dùng cái này nếu cần tái lập số liệu, đừng
  dùng `adapter_v4_final`.

### 2.5 Kết quả nghiên cứu nền (`reports/from_mobile_agent_paper/`)

File kết quả thô (không phải số liệu tự đo): `fresh_locked_repro/` (kết quả
headline + script/notebook đánh giá), `fresh_baseline_comparison/` (bằng
chứng hybrid retrieval không thắng BM25), `ondevice/` (benchmark điện thoại
thật), `execution_pilot/` (Pilot22). Đọc `reports/from_mobile_agent_paper/README.md`
để biết chi tiết, kể cả phần **cố ý không copy** (model điện thoại chính xác
đã thất lạc, ảnh chụp màn hình Pilot22 không copy vì lý do riêng tư).

### 2.6 Hạ tầng tuân thủ (gốc repo)

- `LICENSE` (Apache-2.0): áp dụng cho **toàn bộ repo**, kể cả tài sản nền —
  giảng viên đã xác nhận license cho `from_mobile_agent_paper` (05/08/2026).
- `THIRD_PARTY_NOTICES.md`: liệt kê nguồn/license từng model, thư viện, công
  cụ tham khảo (Qwen2.5, llama.cpp, DroidCall...).
- `CHANGELOG.md`: lịch sử thay đổi theo `Keep a Changelog`.
- `.gitattributes`: theo dõi 2 file `.gguf` (vượt 100MB) qua Git LFS — chạy
  `git lfs install` trước khi commit lần đầu; theo dõi quota LFS miễn phí
  (1GB/tháng) vì khá sát với dung lượng model đang theo dõi.
- `.gitignore`: chặn cache Python/Node, build Android, rác IDE/OS.
- `reports/MAU_BAO_CAO_KET_QUA.md`: khung báo cáo kết quả cuối kỳ.

## 3. Trạng thái hiện tại (tính đến 05/08/2026)

| Hạng mục | Trạng thái |
|---|---|
| Repo GitHub | Có (`dnphuongictu/SV03`), cần commit thật thường xuyên thay vì 1 commit tự động |
| License / THIRD_PARTY_NOTICES / CHANGELOG | ✅ Hoàn tất, license tài sản nền đã được giảng viên xác nhận |
| Git LFS cho model lớn | ✅ Đã cấu hình (`.gitattributes`), nhớ `git lfs install` trước khi commit |
| Release/tag phiên bản | **Chưa có** |
| Validator + test Python/JS | Có, đều pass |
| Web tool gán nhãn | Có, đã chạy thử |
| Dữ liệu | **Chỉ 6/500 câu** — đây là khoảng cách lớn nhất |
| Đánh giá baseline vs cải tiến | **Chưa làm** |
| Đăng ký dự thi (Google Form) | **Chưa xác nhận đã nộp** — hỏi giảng viên |

## 4. Việc cần làm tiếp — theo thứ tự ưu tiên

Chi tiết lộ trình theo tuần: `docs/05_KE_HOACH_DU_THI_PMMN2026.md` mục 5. Tóm
tắt việc cần làm, theo thứ tự:

1. **Xác nhận với giảng viên**: đã nộp phiếu đăng ký dự thi PMMN 2026 cho
   DT03 chưa (`docs/05` mục 0 và mục 4.2 — license tài sản nền đã xong).
2. **Tạo dữ liệu**: từ 6 câu lên tối thiểu 500 câu đã kiểm tra, theo đúng quy
   tắc trong `docs/03_SO_TAY_DU_LIEU.md` — chia việc ngay cho 3 người, hai
   người gán nhãn độc lập, nhớ có văn phong người lớn tuổi và khoá test set
   trước khi augment.
3. **Đánh giá**: baseline rule/template so với một cải tiến duy nhất (đúng
   RQ1–RQ3 trong `docs/02`), viết báo cáo theo `reports/MAU_BAO_CAO_KET_QUA.md`,
   dùng số liệu ở `docs/04` làm điểm neo khi so sánh.
4. **Hoàn thiện PoF**: GitHub Release đầu tiên (`v0.1.0`), dùng GitHub Issues
   làm bug tracker thật, kiểm tra build từ mã nguồn trên máy sạch.
5. **Chuẩn bị demo chung kết**: kịch bản 2–3 phút dùng
   `demo/mockup_nguoi_lon_tuoi.html` hoặc app Android trong
   `demo/android_mockup_nguoi_lon_tuoi/` để minh hoạ trực quan câu chuyện ứng
   dụng, thay vì chỉ nói bằng lời.

## 5. Quy tắc bắt buộc (đừng phá vỡ)

1. `source_code/from_*`, `data/from_*`, `models/from_*`, `reports/from_*` là
   tài sản nền — không sửa trực tiếp, không nhận là đóng góp của nhóm.
2. Không gọi điện/nhắn tin thật; không dùng tên/số điện thoại/địa chỉ thật ở
   bất kỳ đâu (dữ liệu, demo, ảnh chụp màn hình).
3. Ground truth phải độc lập với prediction; test set khoá trước khi augment,
   không chỉnh sửa lại sau khi đã dùng để đánh giá.
4. Mỗi con số trong báo cáo phải có dữ liệu, cấu hình và lệnh tái lập đi kèm.
5. Không đưa dữ liệu nhận dạng/nhạy cảm lên repo công khai.

(Xem đầy đủ tại `../../00_BO_NEN_6_DU_AN.md` ở thư mục `QLSV_NCKH`, áp dụng
chung cho cả 6 đề tài.)

## 6. Lệnh hay dùng

```powershell
# Kiểm định dữ liệu
python src/vidroid_validator.py data/sample_vidroidcall.jsonl

# Test Python
python -m unittest discover -s tests -v

# Web tool gán nhãn
python -m http.server 8000 -d demo
# rồi mở http://localhost:8000 (mockup người lớn tuổi ở mục "Xem mockup..." trên trang)

# Test logic validate JavaScript
node --test
```

## 7. Còn thắc mắc thì hỏi ai

Liên hệ giảng viên phụ trách cuộc thi (xem thông tin trong file thể lệ gốc ở
thư mục `QLSV_NCKH`) hoặc giảng viên hướng dẫn nhóm DT03 để xác nhận tình
trạng đăng ký dự thi — việc này nhóm không tự quyết được, xem mục 4.1.
(License tài sản nền đã được xác nhận, xem mục 2.6.)
