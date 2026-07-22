# ViDroidCall Studio - bộ nền sinh viên

Công cụ tạo và kiểm định dữ liệu câu lệnh tiếng Việt cho Android assistant offline.
Sinh viên tập trung schema, gán nhãn, validator, phân tích lỗi và chống rò rỉ dữ
liệu; không fine-tune SLM trong giai đoạn đầu.

```powershell
cd 03_ViDroid_Assistant_Dataset_Tool
python src/vidroid_validator.py data/sample_vidroidcall.jsonl
python -m unittest discover -s tests -v
```
