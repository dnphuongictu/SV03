# Kế hoạch dự thi "Phát triển phần mềm mã nguồn mở tích hợp AI 2026"

Nguồn thể lệ: `THONG BAO Thể lệ cuộc thi Phát triển phần mềm mã nguồn mở tích hợp
AI 2026-.pdf` (Khoa CNTT, ĐH CNTT&TT - ĐH Thái Nguyên). Đội đăng ký: DT03 —
ViDroidCall Studio (Đỗ Quang Minh, Lê Quang Hưng, Nguyễn Tuấn Anh), repo dự kiến
`https://github.com/dnphuongictu/SV03` (đã tồn tại, 1 commit tính đến
05/08/2026).

## 0. Mốc thời gian còn lại

| Mốc | Ngày |
|---|---|
| Nộp kho mã nguồn sản phẩm | đến **30/09/2026** |
| Chấm kho mã nguồn (tiêu chí PoF, 50đ) | 01–08/10/2026 |
| Chung kết: hackathon + demo (tiêu chí sản phẩm, 50đ) | 14h00 thứ Bảy **10/10/2026**, hội trường tầng 5 nhà C1 |

Cần xác nhận gấp: `.automation/` trong thư mục `QLSV_NCKH` chỉ ghi nhận đã tự
động nộp phiếu đăng ký Google Form cho DT02 và DT06 — **chưa thấy bằng chứng
DT03 đã nộp phiếu đăng ký dự thi thật**. Đây là việc cần giảng viên/nhóm xác
nhận trước, vì cuộc thi chỉ chấm sản phẩm đã đăng ký hợp lệ.

## 1. Điểm PoF (50đ, chấm trước chung kết) — hiện trạng và việc cần làm

| # | Tiêu chí | Điểm | Hiện trạng (05/08/2026) | Việc còn cần làm |
|---|---|---|---|---|
| 1 | Quản lý mã nguồn trên Internet | 5 | Repo GitHub công khai đã có, nhưng chỉ 1 commit (có vẻ do script tự động) | Dùng git thật trong suốt quá trình làm (nhiều commit có ý nghĩa), tránh bị đánh giá "trên thực tế không được sử dụng" |
| 2 | Giấy phép OSI-approved | 10 | ✅ Đã có `LICENSE` (Apache-2.0) + `THIRD_PARTY_NOTICES.md`; giảng viên đã xác nhận giấy phép cho tài sản nền `from_mobile_agent_paper` (05/08/2026) | Không còn — chỉ cần giữ nguyên khi thêm file mới |
| 3 | Có bản release | 5 | Chưa có release/tag nào | Tạo GitHub Release có tag phiên bản (vd `v0.1.0`) trước hạn nộp, dùng định dạng mở, có release note |
| 4 | Build from source | 10 | ✅ README đã có hướng dẫn cài đặt từ `git clone`, đã test không phụ thuộc đường dẫn cố định | Kiểm tra lại một lần trên máy sạch/tài khoản khác trước khi nộp |
| 5 | Thư viện/gói đính kèm | 10 | ✅ Đã có `THIRD_PARTY_NOTICES.md` liệt kê nguồn/license từng model/thư viện; đã thêm `.gitattributes` dùng Git LFS cho 2 file GGUF vượt 100MB | Cài `git lfs install` trước khi commit; theo dõi quota LFS miễn phí (1GB/tháng) — xem README |
| 6 | Tài liệu & giao tiếp | 10 | ✅ Có `CHANGELOG.md`, README đầy đủ hơn; **chưa dùng GitHub Issues thật** | Bật/dùng GitHub Issues thật cho quản lý task nhóm, không chỉ để trống |

## 2. Điểm sản phẩm (50đ, chấm tại chung kết)

| # | Tiêu chí | Điểm | Ghi chú áp dụng cho ViDroidCall Studio |
|---|---|---|---|
| 1 | Tính nguyên gốc giải pháp | 10 | Khi demo, tách rõ phần **nền** (pipeline/model nghiên cứu trong `from_mobile_agent_paper`) khỏi phần **sinh viên tự làm** (web tool gán nhãn, validator, schema, 500+ câu dữ liệu mới) — giám khảo cần thấy rõ đâu là đóng góp thật |
| 2 | Mức độ hoàn thiện | 10 | **Rủi ro lớn nhất hiện nay**: `demo/` đang trống, chỉ có validator CLI 43 dòng và 6 câu mẫu, còn xa mục tiêu tối thiểu (web tool + 500 câu đã kiểm tra, theo `docs/00_HUONG_DAN_GIANG_VIEN_VA_SINH_VIEN.md`) |
| 3 | Thân thiện người dùng | 10 | Web tool cần báo lỗi ngay khi nhập liệu, không cần tài khoản/cài đặt phức tạp để demo tại chỗ |
| 4 | Khả năng tích hợp AI | 10 | Tên cuộc thi nhấn "tích hợp AI" — nên demo trực tiếp một SLM nhỏ (Gemma-3-270M-IT hoặc Qwen2.5-0.5B GGUF, đã có sẵn trong `models/`) chạy ngay trong tool để gợi ý paraphrase/validate, kèm tài liệu kỹ thuật (`docs/04_KET_QUA_NGHIEN_CUU_NEN.md`) và mockup tương tác `demo/mockup_nguoi_lon_tuoi.html` cho thấy dữ liệu/schema (`risk_level`, xác nhận lại lệnh) chuyển thành UX thật thế nào |
| 5 | Trình diễn & thu hút cộng đồng | 10 | Chuẩn bị kịch bản demo ngắn (2–3 phút): mở `demo/mockup_nguoi_lon_tuoi.html`, bấm qua 3 tình huống (lệnh an toàn tự thực hiện / lệnh rủi ro cần xác nhận / lệnh thiếu thông tin cần hỏi lại) để giám khảo thấy ngay câu chuyện ứng dụng ở mục 3 mà không cần giải thích bằng lời |

## 3. Định vị "tính ứng dụng": trợ lý giọng nói tối giản thao tác cho người lớn tuổi

**Đối tượng người dùng cụ thể**: người lớn tuổi dùng smartphone Android phổ
thông — thao tác chạm/gõ khó khăn (run tay, mắt kém), ít quen giao diện nhiều
lớp menu, và quan trọng nhất: **e ngại khi máy tự làm gì đó mà mình không chắc
đã nói đúng** (sợ gọi nhầm người, gửi nhầm tin). Đây là khoảng trống thật:
phần lớn trợ lý giọng nói thương mại tối ưu cho người dùng trẻ, thao tác nhanh,
không có bước xác nhận rõ ràng bằng ngôn ngữ tự nhiên trước khi thực thi.

**Vì sao vừa ứng dụng vừa khoa học, không cần đổi phạm vi dữ liệu:**

- Schema hiện có (`risk_level`, và trường `requires_confirmation` trong định
  dạng tool-call của `VIntentAgent` — xem
  `source_code/from_mobile_agent_paper/README.md`) **đã sẵn đúng cơ chế** cần
  cho hướng này: lệnh rủi ro thấp (`set_alarm`, `set_timer`) thực hiện ngay,
  lệnh rủi ro trung bình/cao (`call_contact`, `send_sms`) bắt buộc đọc lại
  bằng câu tự nhiên và chờ một trong hai nút to "Đúng/Không phải" — không cần
  gõ, không cần điều hướng menu.
- Số liệu **Confirmation Accuracy = 0.944** (Fresh126, xem
  `docs/04_KET_QUA_NGHIEN_CUU_NEN.md` mục 2) là bằng chứng có sẵn, không phải
  suy diễn, cho thấy bước xác nhận này khả thi về mặt kỹ thuật.
- Khi viết 500 câu dữ liệu, chủ động thêm **văn phong người lớn tuổi thật**:
  câu dài, vòng vo, có từ đệm ("À, cháu ơi...", "Cho bác hỏi..."), gọi tên ứng
  dụng không đúng thuật ngữ ("cái ứng dụng bản đồ ấy") — xem hướng dẫn gán
  nhãn cụ thể tại `03_SO_TAY_DU_LIEU.md`. Đo intent/slot accuracy riêng trên
  nhóm câu này là một lát cắt đo được, mở rộng tự nhiên của RQ2
  (`02_DE_CUONG_NCKH_TOI_THIEU.md`).
- Hướng nghiên cứu mở rộng (tùy chọn, không bắt buộc cho bản nộp đầu): đo xem
  bước xác nhận lại bắt được thêm bao nhiêu % lỗi mà validator/schema bỏ sót
  (JSON hợp lệ về cấu trúc nhưng sai slot) — mở rộng RQ1 hiện có bằng một cột
  "accuracy sau xác nhận" bên cạnh "accuracy trước xác nhận" trên cùng test
  set khóa.

**Minh hoạ trực quan**: `demo/mockup_nguoi_lon_tuoi.html` — mockup tương tác
(không phải công cụ gán nhãn cho sinh viên, đây là giao diện minh hoạ phía
người dùng cuối) mô phỏng 3 luồng: lệnh an toàn tự thực hiện, lệnh rủi ro cần
xác nhận bằng 2 nút to, và lệnh thiếu thông tin cần hỏi lại bằng giọng nói.
Dùng để trình chiếu tại chung kết, không cần cài đặt gì (mở thẳng bằng trình
duyệt hoặc qua `python -m http.server 8000 -d demo`).

Đã có thêm **bản Android thật** tại `demo/android_mockup_nguoi_lon_tuoi/` —
build bằng Gradle thành công, cài và chạy thử trên máy ảo Android không lỗi
(có ảnh chụp màn hình thật trong thư mục đó), dùng `SpeechRecognizer` +
`TextToSpeech` thật của Android thay vì giả lập bằng nút bấm. Đây là lựa chọn
mạnh hơn cho phần trình diễn tại chung kết nếu nhóm muốn "cầm điện thoại lên
demo thật" thay vì mở trình duyệt — nhưng vẫn chỉ là bản trình diễn UX
(không dùng SLM/model AI thật để nhận diện intent, chỉ so khớp từ khoá), nhóm
cần tự quyết định có đầu tư tiếp hướng này hay không.

Vẫn giữ đúng giới hạn đã ghi trong `MODEL_RUNTIME_DECISION.md` — không tuyên
bố NPU hay production-ready khi chưa đo thật; mockup là minh hoạ UX, không
phải tuyên bố đã có ứng dụng Android hoàn chỉnh.

## 4. Rủi ro cần xử lý sớm nhất

1. ~~**License**~~ — **đã xử lý (05/08/2026)**: `LICENSE` (Apache-2.0) +
   `THIRD_PARTY_NOTICES.md` đã có, giảng viên đã xác nhận license cho tài sản
   nền `from_mobile_agent_paper`. Repo đã đủ điều kiện công bố công khai.
2. **Đăng ký dự thi**: xác nhận DT03 đã nộp phiếu đăng ký Google Form thật
   (xem mục 0) — **vẫn còn treo**, ưu tiên cao nhất hiện tại.
3. **Khối lượng dataset**: từ 6 câu lên 500 câu đã kiểm tra là khoảng cách lớn
   nhất về khối lượng công việc — cần chia việc ngay cho 3 thành viên thay vì
   để tới gần hạn.
4. **Git LFS**: 2 file `.gguf` trong `models/from_mobile_agent_paper/` vượt
   giới hạn 100MB/file của GitHub, đã cấu hình `.gitattributes` dùng Git LFS —
   nhớ chạy `git lfs install` trước khi commit lần đầu, và theo dõi quota LFS
   miễn phí (1GB lưu trữ + 1GB băng thông/tháng, khá sát với ~850MB đang theo
   dõi).

## 5. Lộ trình rút gọn (05/08 – 30/09/2026)

- **Tuần 1–2**: xác nhận đăng ký dự thi (mục 4.2 — license đã xử lý xong).
- **Tuần 3–5**: xây web tool gán nhãn, thu thập/viết 500 câu, hai người gán
  nhãn độc lập, khóa test set trước khi augment (theo `03_SO_TAY_DU_LIEU.md`).
- **Tuần 6**: đánh giá baseline rule/template so với một cải tiến duy nhất
  (theo `02_DE_CUONG_NCKH_TOI_THIEU.md`), viết báo cáo theo mẫu
  `reports/MAU_BAO_CAO_KET_QUA.md`.
- **Tuần 7**: tạo GitHub Release `v0.1.0`, viết `CHANGELOG.md`, hoàn thiện
  README và demo tích hợp AI (mục 2.4).
- **Tuần 8 (đến 30/09)**: buffer — test build trên máy sạch/thư mục khác,
  chuẩn bị kịch bản demo cho chung kết 10/10/2026.
