# ViDroidCall Studio - Chuan bi du lieu, bai bao va mo hinh

## Bo nen sinh vien

Bat dau tai `../README.md`, chay validator tren `data/sample_vidroidcall.jsonl`,
roi doc `00_HUONG_DAN_GIANG_VIEN_VA_SINH_VIEN.md` va `03_SO_TAY_DU_LIEU.md`.

## 1. Bai toan

Xay dung cong cu tao du lieu cau lenh tieng Viet cho tro ly Android offline. Sinh vien tap trung vao dataset, schema, validator va giao dien gan nhan; khong can fine-tune SLM trong giai doan dau.

## 2. Du lieu can chuan bi

### Nhom intent ban dau

| Nhom | Intent/action | Vi du |
|---|---|---|
| Bao thuc | `set_alarm` | "Dat bao thuc 6 gio sang mai" |
| Hen gio | `set_timer` | "Hen 10 phut nua nhac toi" |
| Goi dien | `call_contact` | "Goi cho me" |
| SMS | `send_sms` | "Nhan cho An la toi den muon" |
| Ban do | `open_map` | "Chi duong den truong" |
| Mo app | `open_app` | "Mo YouTube" |
| Khong ho tro | `unsupported` | "Dat ve may bay re nhat" |
| Thieu thong tin | `clarify` | "Nhan cho Nam" |

Da co file mau tai `data/sample_vidroidcall.jsonl`.

## 3. Bai bao/tai lieu can doc

1. Tai lieu noi bo: VIntentAgent trong `mobile_agent_paper`. Ket qua thuc
   nghiem moi nhat (ToolAcc, E2E, on-device that, ket luan da kiem dinh thong
   ke) da duoc tom tat tai `04_KET_QUA_NGHIEN_CUU_NEN.md` — doc truoc khi lam
   RQ1-RQ3 de tranh lap lai thi nghiem da co ket luan.
2. Android Common Intents: https://developer.android.com/guide/components/intents-common
3. Android App Actions overview: https://developer.android.com/develop/devices/assistant/app-actions/overview
4. llama.cpp grammar/GBNF constrained decoding: https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md
5. Qwen2.5 0.5B Instruct GGUF de tham khao SLM nho: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF

## 4. Mo hinh nen/nen dung

| Muc dich | Model | Dinh dang |
|---|---|---|
| Baseline sinh JSON | Rule/template | Khong can model |
| Goi y paraphrase | Gemma-3-270M-IT | GGUF Q4_K_M |
| Goi y paraphrase thay the | Qwen2.5-0.5B-Instruct | GGUF Q4_K_M |
| Kiem tra schema | JSON Schema/Zod | Khong can model |

Khuyen nghi cho cuoc thi: neu chua chay duoc local SLM, dung API tuy chon cho demo paraphrase, nhung san pham chinh van la dataset tool ma nguon mo.

## 5. Viec can lam tuan dau

1. Thiet ke schema JSON cho 8 intent dau.
2. Tao form nhap cau lenh, chon intent, nhap tham so.
3. Viet validator cho ngay gio, sdt, ten lien he, truong bat buoc.
4. Tao 100 cau mau dau tien.
5. Xuat JSONL/CSV.

## 6. Ket qua toi thieu

- Web tool gan nhan.
- 500 cau tieng Viet da kiem tra.
- Bao cao loi: thieu tham so, nhap nhang, cau khong ho tro.
