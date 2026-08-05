# Third-party notices

`LICENSE` (Apache-2.0) ở gốc repo áp dụng cho **toàn bộ repo**, bao gồm cả
phần do nhóm sinh viên DT03 tự viết (`src/`, `tests/`, `demo/`,
`data/vidroidcall.schema.json`, `data/sample_vidroidcall.jsonl`, tài liệu
trong `docs/`) và tài sản nền trong các thư mục `source_code/from_*`,
`data/from_*`, `models/from_*`, `reports/from_*`.

**Xác nhận giấy phép (05/08/2026)**: giảng viên hướng dẫn/tác giả dự án
nghiên cứu gốc `mobile_agent_paper` đã đồng ý cấp phép Apache-2.0 cho toàn bộ
tài sản nền sao chép vào repo này (`source_code/from_mobile_agent_paper`,
`data/from_mobile_agent_paper`, `models/from_mobile_agent_paper`,
`reports/from_mobile_agent_paper`) — cùng giấy phép với phần sinh viên tự
viết, tương thích với Qwen2.5 (Apache-2.0) và llama.cpp/DroidCall (MIT). Repo
có thể coi là đã rõ giấy phép để công bố công khai.

## Model / dataset / công cụ tham chiếu

| Tên | Vai trò trong dự án | Giấy phép | Nguồn |
|---|---|---|---|
| Qwen2.5-0.5B-Instruct / 1.5B-Instruct | Model nền dùng làm baseline sinh JSON/paraphrase | Apache-2.0 | https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct |
| llama.cpp / llama-cpp-python | Runtime chạy GGUF trên máy tính và Android | MIT | https://github.com/ggml-org/llama.cpp |
| DroidCall dataset | Tham khảo format câu lệnh/schema function-calling Android (tiếng Anh) | MIT | https://github.com/UbiquitousLearning/DroidCall |
| Gemma-3-270M-IT (GGUF, khuyến nghị, chưa dùng trong bản hiện tại) | Gợi ý paraphrase | Gemma Terms of Use (không phải giấy phép OSI-approved cổ điển — cần đọc kỹ điều khoản trước khi dùng cho bản dự thi) | https://huggingface.co/unsloth/gemma-3-270m-it-GGUF |
| SmolLM2-360M-Instruct (GGUF, khuyến nghị, chưa dùng) | Phương án siêu nhẹ | Apache-2.0 | https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF |

Ghi chú: các model GGUF (`.gguf`) trong `models/from_mobile_agent_paper/` là
bản nén (quantize) không chỉnh sửa trọng số gốc ngoài lượng tử hóa Q4_K_M —
không vi phạm điều khoản "mã nguồn của gói đính kèm đã bị chỉnh sửa" vì đây là
quy trình lượng tử hóa chuẩn của llama.cpp, không phải chỉnh sửa tùy ý.

Không có thư viện Python bên ngoài nào được bundle trực tiếp trong repo; phần
`src/` của nhóm chỉ dùng thư viện chuẩn (standard library). `demo/` (trừ
`demo/android_mockup_nguoi_lon_tuoi/`) là HTML/CSS/JavaScript thuần, không phụ
thuộc gói ngoài, không cần bước cài đặt.

`demo/android_mockup_nguoi_lon_tuoi/` (app Android build thử) khai báo phụ
thuộc qua Gradle, tự tải từ Maven Central/Google khi build, không bundle mã
nguồn thư viện: `androidx.appcompat:appcompat` (Apache-2.0),
`androidx.core:core-ktx` (Apache-2.0), `com.google.android.material:material`
(Apache-2.0). Dùng `android.speech.SpeechRecognizer` và
`android.speech.tts.TextToSpeech` — API hệ thống Android, không phải thư viện
đính kèm.
