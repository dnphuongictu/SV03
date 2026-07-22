# Du lieu - ViDroidCall Studio

Schema sinh vien: `vidroidcall.schema.json`. Chay
`python src/vidroid_validator.py data/sample_vidroidcall.jsonl` truoc khi nhap
du lieu vao train/validation/test. Khong sua truc tiep `from_mobile_agent_paper`.

## File chinh

- `sample_vidroidcall.jsonl`: du lieu mau JSON Lines.
- `exports/`: dataset nhom xuat ra.
- `schemas/`: JSON schema cho tung intent.

## Truong toi thieu

- `id`
- `utterance`
- `language`
- `intent`
- `arguments`
- `risk_level`
- `split`
- `notes`

Moi dong JSONL la mot mau rieng.
