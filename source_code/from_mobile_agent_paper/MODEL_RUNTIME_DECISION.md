# Quyết định model và runtime

## Model chính

### Cấu hình siêu nhẹ

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Giấy phép: Apache-2.0.
- Vai trò: kiểm tra giới hạn thấp nhất về RAM, latency và chất lượng.
- Định dạng triển khai: GGUF Q4_K_M.

### Cấu hình cân bằng

- Model: `Qwen/Qwen2.5-1.5B-Instruct`
- Giấy phép: Apache-2.0.
- Vai trò: baseline chất lượng và model fine-tune chính.
- Định dạng triển khai: GGUF Q4_K_M.

### Baseline đối chiếu

- `Qwen/Qwen2.5-1.5B-Instruct` FP16/BF16 trên máy tính.
- Q4_K_M trên cùng tập test để đo suy giảm do quantization.
- PhoneLM-0.5B/1.5B chỉ thêm khi checkpoint, tokenizer và giấy phép được
  xác nhận phù hợp.

## Lý do chọn

- Có kích thước 0.5B và 1.5B đúng hai mức thực nghiệm.
- Hỗ trợ đa ngôn ngữ, gồm tiếng Việt.
- Model card công bố context dài và khả năng sinh JSON có cấu trúc.
- Apache-2.0 thuận lợi cho nghiên cứu và phát hành artifact.
- Có hệ sinh thái Transformers và GGUF/llama.cpp rộng.

## Runtime chính

### Máy tính

- `llama.cpp` hoặc `llama-cpp-python`.
- Dùng để chạy nhanh baseline GGUF và kiểm tra prompt/evaluator.

### Android

- `llama.cpp` Android làm runtime đầu tiên.
- Backend CPU là baseline tái lập được trên nhiều thiết bị.
- Vulkan chỉ bật thành một biến thực nghiệm sau khi CPU pipeline ổn định.
- Không tuyên bố NPU nếu chưa có backend và phép đo NPU thật.

## Quantization

- FP16/BF16: trần chất lượng trên máy tính.
- Q8_0: mức trung gian.
- Q4_K_M: cấu hình triển khai chính.
- Không dùng Q2/Q1.x trong phiên bản đầu vì rủi ro làm sai tool/arguments.

## Nguồn chính thức

- Qwen2.5-0.5B-Instruct:
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- Qwen2.5-1.5B-Instruct:
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
- llama.cpp:
  https://github.com/ggml-org/llama.cpp
- DroidCall:
  https://github.com/UbiquitousLearning/DroidCall

## Điều kiện đổi quyết định

Chỉ đổi model nếu một ứng viên khác đồng thời:

1. Có giấy phép tương đương hoặc dễ sử dụng hơn.
2. Chạy được cùng runtime Android.
3. Có footprint không lớn hơn.
4. Tăng End-to-End Task Success đáng kể trên cùng ViDroidCall.

