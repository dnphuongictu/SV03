# Models - ViDroidCall Studio

## Tai san nen da co san

`from_mobile_agent_paper/adapter_v8` la adapter LoRA dung de tao ra ket qua
headline Fresh126 (ToolAcc 0.746) trong `docs/04_KET_QUA_NGHIEN_CUU_NEN.md`.
`from_mobile_agent_paper/adapter_v4_final` la ban cu hon, giu lai de tham
khao/so sanh nhung khong phai adapter tao ra so lieu headline. Dung dung
adapter_v8 neu can tai lap dung so lieu paper.

## Model khuyen nghi

1. Gemma-3-270M-IT GGUF Q4_K_M
   - Link: https://huggingface.co/unsloth/gemma-3-270m-it-GGUF
   - Dung cho: goi y paraphrase, viet lai cau tieng Viet.

2. Qwen2.5-0.5B-Instruct GGUF Q4_K_M
   - Link: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
   - Dung cho: so sanh kha nang sinh JSON/intent.

3. SmolLM2-360M-Instruct GGUF Q4_K_M
   - Link: https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF
   - Dung cho: phuong an sieu nhe.

## Luu y

Phien ban sinh vien khong can fine-tune. Diem chinh la:

- Schema tot.
- Validator tot.
- Dataset tieng Viet sach.
- Chia train/validation/test-ID/test-OOD ro rang.
