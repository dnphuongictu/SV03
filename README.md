# ViDroidCall Studio - bộ nền sinh viên

Công cụ tạo và kiểm định dữ liệu câu lệnh tiếng Việt cho Android assistant offline.
Sinh viên tập trung schema, gán nhãn, validator, phân tích lỗi và chống rò rỉ dữ
liệu; không fine-tune SLM trong giai đoạn đầu.

**Sinh viên nhận bàn giao workspace này: đọc
[`docs/06_BAN_GIAO_SINH_VIEN.md`](docs/06_BAN_GIAO_SINH_VIEN.md) trước tiên**
— mục tiêu dự án, bản đồ toàn bộ workspace, và việc cần làm tiếp theo thứ tự
ưu tiên.

Kết quả thực nghiệm nền (ToolAcc, E2E, on-device thật) từ dự án nghiên cứu gốc
đã được tổng hợp tại [`docs/04_KET_QUA_NGHIEN_CUU_NEN.md`](docs/04_KET_QUA_NGHIEN_CUU_NEN.md).

Kế hoạch dự thi "Phát triển phần mềm mã nguồn mở tích hợp AI 2026" (mốc thời
gian, đối chiếu tiêu chí chấm điểm, việc cần làm) tại
[`docs/05_KE_HOACH_DU_THI_PMMN2026.md`](docs/05_KE_HOACH_DU_THI_PMMN2026.md).

Định vị ứng dụng: trợ lý giọng nói tối giản thao tác cho **người lớn tuổi**
(giọng nói + vài nút to, xác nhận lại lệnh rủi ro trước khi thực thi) — xem
mockup tương tác [`demo/mockup_nguoi_lon_tuoi.html`](demo/mockup_nguoi_lon_tuoi.html)
và chi tiết tại `docs/05_KE_HOACH_DU_THI_PMMN2026.md` mục 3. Đã có bản build
thử app Android thật (giọng nói + Text-to-Speech thật, đã cài và chạy được
trên máy ảo, không crash) tại
[`demo/android_mockup_nguoi_lon_tuoi/`](demo/android_mockup_nguoi_lon_tuoi/README.md).

## Giấy phép

Mã nguồn/tài liệu do nhóm tự viết (`src/`, `tests/`, `demo/`, `docs/`,
`data/vidroidcall.schema.json`) theo giấy phép Apache-2.0 — xem `LICENSE`.
Tài sản nền (`source_code/from_*`, `data/from_*`, `models/from_*`) giữ nguyên
trạng license gốc, xem `THIRD_PARTY_NOTICES.md` (**có mục cảnh báo cần giảng
viên xác nhận trước khi nộp bài dự thi**).

## Cài đặt và chạy từ mã nguồn

Yêu cầu: Python ≥ 3.9 (chỉ dùng thư viện chuẩn, không cần `pip install` gì
thêm cho `src/`). Không phụ thuộc đường dẫn tuyệt đối — chạy được sau khi
`git clone` vào bất kỳ thư mục nào.

Kho có 2 file model GGUF vượt giới hạn 100MB/file của GitHub
(`models/from_mobile_agent_paper/*.gguf`) — đã cấu hình theo dõi qua
[Git LFS](https://git-lfs.com/) trong `.gitattributes`. Cài Git LFS một lần
trước khi commit các file này:

```powershell
git lfs install
```

⚠️ Gói LFS miễn phí của GitHub chỉ có 1GB lưu trữ + 1GB băng thông/tháng —
riêng 2 file `.gguf` đã ~850MB, vài lượt clone của giám khảo/sinh viên là có
thể vượt quota và bị chặn tải. Theo dõi dung lượng dùng tại Settings > Billing
> Git LFS Data của repo GitHub, và cân nhắc phương án host model rời (Hugging
Face) nếu quota là vấn đề thật.

```powershell
git clone https://github.com/dnphuongictu/SV03.git
cd SV03

# 1) Kiểm định dữ liệu mẫu
python src/vidroid_validator.py data/sample_vidroidcall.jsonl

# 2) Chạy test Python
python -m unittest discover -s tests -v

# 3) Chạy công cụ web gán nhãn (tĩnh, không cần cài gì thêm)
python -m http.server 8000 -d demo
# rồi mở http://localhost:8000 trên trình duyệt

# 4) (tuỳ chọn) chạy test logic validate phía JavaScript, cần Node.js >= 18
node --test
```

## Cấu trúc

- `src/vidroid_validator.py`: validator CLI (Python, chuẩn cho pipeline/CI).
- `demo/`: web tool gán nhãn tĩnh (HTML/CSS/JS thuần), dùng lại đúng luật
  kiểm định trong `demo/validate.js` (cổng JS của `src/vidroid_validator.py`).
  `demo/mockup_nguoi_lon_tuoi.html` là mockup UX minh hoạ phía người dùng cuối
  (người lớn tuổi), tách biệt với công cụ gán nhãn.
  `demo/android_mockup_nguoi_lon_tuoi/` là bản Android thật của cùng mockup
  (Kotlin, SpeechRecognizer + TextToSpeech thật) — đã build và chạy thử
  thành công, xem README riêng trong thư mục đó.
- `data/vidroidcall.schema.json`: JSON Schema cho một dòng dữ liệu.
- `docs/`: hướng dẫn, đề cương NCKH, sổ tay dữ liệu, kết quả nghiên cứu nền,
  kế hoạch dự thi.
- `source_code/from_*`, `data/from_*`, `models/from_*`, `reports/from_*`: tài
  sản nền do giảng viên cung cấp, không sửa trực tiếp (xem
  `../00_BO_NEN_6_DU_AN.md`).

## Theo dõi lỗi và đóng góp

Dùng GitHub Issues của repo này làm bug tracker. Xem `CHANGELOG.md` cho lịch
sử thay đổi theo phiên bản.
