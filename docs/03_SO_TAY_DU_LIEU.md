# Sổ tay dữ liệu ViDroidCall

Mỗi dòng JSONL là một object theo `data/vidroidcall.schema.json`. ID không trùng;
utterance không rỗng; intent thuộc 8 loại; arguments đủ trường bắt buộc. `clarify`
phải chỉ ra trường thiếu. Câu trùng/chuẩn hóa tương đương không được nằm ở nhiều
split. Tách test trước augmentation và giữ test khóa.

Không dùng tên, số điện thoại, địa chỉ thật. Dùng liên hệ giả như An/Mẹ và địa
điểm công cộng. Mọi câu gọi/SMS chỉ là dữ liệu, không được thực thi. Data card cần
ghi nguồn, người gán nhãn, guideline, phân bố intent, mức rủi ro và hạn chế.
