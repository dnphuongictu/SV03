# Đề cương NCKH - ViDroidCall

**RQ1:** validator và constrained schema giảm tỷ lệ JSON/action không hợp lệ bao
nhiêu? **RQ2:** dữ liệu tiếng Việt có nhiễu/code-switch ảnh hưởng thế nào đến
intent accuracy và slot exact match? **RQ3:** targeted augmentation có cải thiện
tập test khóa mà không gây leakage không?

So sánh rule/template baseline với phương pháp cải tiến trên cùng test set đã khóa.
Báo intent accuracy, macro-F1, slot exact match, valid JSON rate, unsafe action
rate và latency. Không điều chỉnh theo test. Tệp `from_mobile_agent_paper` là tài
sản nền; đóng góp sinh viên là tool, guideline, dữ liệu mới và thí nghiệm áp dụng.
