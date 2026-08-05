# Sổ tay dữ liệu ViDroidCall

Mỗi dòng JSONL là một object theo `data/vidroidcall.schema.json`. ID không trùng;
utterance không rỗng; intent thuộc 8 loại; arguments đủ trường bắt buộc. `clarify`
phải chỉ ra trường thiếu. Câu trùng/chuẩn hóa tương đương không được nằm ở nhiều
split. Tách test trước augmentation và giữ test khóa.

Không dùng tên, số điện thoại, địa chỉ thật. Dùng liên hệ giả như An/Mẹ và địa
điểm công cộng. Mọi câu gọi/SMS chỉ là dữ liệu, không được thực thi. Data card cần
ghi nguồn, người gán nhãn, guideline, phân bố intent, mức rủi ro và hạn chế.

## Văn phong người lớn tuổi (bắt buộc có trong 500 câu)

Dự án định vị ứng dụng cho người dùng lớn tuổi (xem
`05_KE_HOACH_DU_THI_PMMN2026.md`, mục 3) — vì vậy tập dữ liệu phải phản ánh
đúng cách người lớn tuổi thật sự nói, không chỉ câu lệnh ngắn gọn kiểu người
dùng trẻ. Khi viết câu, chủ động đưa vào (mục tiêu tối thiểu: khoảng 1/4 số câu
theo nhóm phong cách này):

- **Câu dài, vòng vo, có từ đệm**: "À, cháu ơi cho bác hỏi mấy giờ rồi ấy nhỉ,
  bác muốn đặt báo thức 6 giờ sáng mai" thay vì "Đặt báo thức 6 giờ sáng mai".
- **Gọi tên ứng dụng/chức năng không đúng thuật ngữ**: "cái ứng dụng bản đồ
  ấy", "cái nút gọi điện" thay vì "Google Maps", "Phone".
- **Xưng hô lịch sự, gián tiếp**: dùng "bác", "cho tôi hỏi", "làm ơn" thay vì
  ra lệnh trực tiếp.
- Vẫn phải gán đúng `intent`/`arguments` như câu chuẩn — phần vòng vo không
  được đưa vào `arguments`, chỉ giữ trong `utterance`.
- Đánh dấu các câu này trong trường `notes` (vd `"elderly_style"`) để có thể
  lọc riêng khi phân tích intent/slot accuracy theo nhóm phong cách — đây là
  một lát cắt đo được, không chỉ là gia vị cho câu chuyện demo.

## Gán `risk_level` theo mức hậu quả nếu xác nhận sai (không theo cảm tính)

Vì UX mục tiêu là "xác nhận lại bằng giọng nói trước khi thực thi lệnh rủi ro"
(xem mockup `demo/mockup_nguoi_lon_tuoi.html`), `risk_level` phải phản ánh
đúng mức cần bước xác nhận, thống nhất giữa hai người gán nhãn:

| Intent | risk_level mặc định | Vì sao |
|---|---|---|
| `set_alarm`, `set_timer` | low | Sai thì chỉnh lại dễ, không ảnh hưởng người khác |
| `open_map`, `open_app` | low–medium | Sai thì mở nhầm màn hình, không gây hậu quả với người khác |
| `call_contact`, `send_sms` | medium–high | Sai thì gọi/nhắn nhầm người — hậu quả khó thu hồi với người lớn tuổi |
| `clarify`, `unsupported` | theo ngữ cảnh câu gốc | Giữ mức rủi ro của hành vi đang được hỏi lại/từ chối |

Khi hai người gán nhãn chọn `risk_level` khác nhau cho cùng một câu, ghi lại
lý do bất đồng vào data card (không tự ý chọn mức thấp hơn cho nhanh).

## Trường bắt buộc và chống rò rỉ

- `id` không trùng; `utterance` không rỗng; `intent` thuộc 8 loại đã định
  nghĩa trong `vidroidcall.schema.json`.
- `clarify` phải chỉ ra trường còn thiếu trong `arguments.missing`.
- Câu trùng hoặc chuẩn hóa tương đương (bỏ dấu câu, viết hoa/thường) không
  được nằm ở nhiều split khác nhau — `src/vidroid_validator.py` và
  `demo/validate.js` đã kiểm tra tự động điều này.
- Tách test trước khi augment dữ liệu và giữ nguyên test đã khóa, không chỉnh
  sửa lại sau khi đã dùng để đánh giá (đúng nguyên tắc Fresh126 của dự án nền,
  xem `04_KET_QUA_NGHIEN_CUU_NEN.md` mục 1).

## Đạo đức và an toàn dữ liệu

Không dùng tên, số điện thoại, địa chỉ thật. Dùng liên hệ giả như An/Mẹ và địa
điểm công cộng. Mọi câu gọi/SMS chỉ là dữ liệu, không được thực thi. Data card
cần ghi nguồn, người gán nhãn, guideline, phân bố intent, mức rủi ro và hạn
chế.
