# VIntentAgent Prototype

## Phạm vi phiên bản đầu

VIntentAgent nhận một yêu cầu tiếng Việt hoặc tiếng Anh và trả về đúng một
lời gọi công cụ Android có cấu trúc:

```json
{
  "tool": "ACTION_SET_ALARM",
  "arguments": {
    "EXTRA_HOUR": 6,
    "EXTRA_MINUTES": 30,
    "EXTRA_MESSAGE": "đi học"
  },
  "requires_confirmation": false
}
```

Nếu yêu cầu thiếu thông tin, không được hỗ trợ hoặc có độ tin cậy thấp:

```json
{
  "tool": null,
  "arguments": {},
  "requires_confirmation": false,
  "status": "clarification",
  "message": "Bạn muốn đặt báo thức lúc mấy giờ?"
}
```

## Câu hỏi nghiên cứu của prototype

1. Top-k tool retrieval có giảm prompt và giữ được độ chính xác không?
2. Constrained output và validator có loại bỏ lỗi cấu trúc/tham số không?
3. INT4 có giảm RAM và độ trễ mà vẫn giữ chất lượng Intent không?

## Ngoài phạm vi

- Điều khiển GUI bằng ảnh.
- Chuỗi tác vụ dài.
- MoE hoặc suy luận phân tán.
- Học tăng cường.
- Huấn luyện foundation model từ đầu.

## Cấu trúc

- `data/tools/android_tools.json`: 24 tool schema song ngữ.
- `data/eval/vi_smoke_test.jsonl`: bộ kiểm thử nhanh tiếng Việt.
- `src/evaluate.py`: evaluator độc lập, chỉ dùng Python standard library.
- `src/retrieve.py`: lexical/BM25-like tool retriever baseline.
- `src/rule_baseline.py`: baseline tất định để kiểm tra pipeline.
- `results/`: prediction và báo cáo thực nghiệm.

