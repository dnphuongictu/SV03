# Hướng dẫn ViDroidCall Studio

## Sản phẩm

Web tool nhập câu lệnh, intent, arguments và split; kiểm tra lỗi ngay khi nhập;
xuất JSONL chuẩn và dashboard phân bố/lỗi. Pipeline/model trong
`source_code/from_mobile_agent_paper` là nền giảng viên, không phải phần sinh viên
viết lại.

## Lộ trình 8 tuần

1. Chạy validator trên sáu câu mẫu, hiểu intent và arguments.
2. Xây form và validation cho 8 intent.
3. Tạo 100 câu sạch, có code-switch, câu thiếu tham số và unsupported.
4. Hai người gán nhãn độc lập; giải quyết bất đồng và ghi guideline.
5. Khóa test set trước khi sửa rule/model; kiểm tra trùng và paraphrase leakage.
6. Đánh giá rule/template baseline: intent accuracy, slot exact match, valid JSON.
7. Thử một cải tiến: noisy text, constrained decoding hoặc retrieval.
8. Nộp tool, 500 câu đã kiểm tra, data card và báo cáo lỗi.

Không chạy lệnh gọi/SMS thật. Action trung bình/cao phải có bước xác nhận trong
thiết kế. Không dùng danh bạ, số điện thoại hoặc tin nhắn thật.
