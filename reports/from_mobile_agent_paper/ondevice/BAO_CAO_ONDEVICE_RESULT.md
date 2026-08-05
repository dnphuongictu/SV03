# Báo cáo kết quả On-Device — Phase 2A hoàn tất

**Ngày**: 10/06/2026
**Model**: vidroidcall v2.1 (Qwen2.5-1.5B + LoRA r=16, 10 epochs)

---

## So sánh kết quả

| Metric | v4 (cũ) | v2.1 (mới) | Cải thiện |
|--------|:-------:|:----------:|:---------:|
| **Tool Selection** | 78.1% | **93.8%** | +15.6% 🎯 |
| **Schema Valid** | 96.9% | **96.9%** | — |
| **Argument Accuracy** | 70.7% | **92.7%** | +22.0% |
| **E2E Task Success** | **0.625** | **0.906** | +28.1% 🚀 |

## Chi tiết theo nhóm

| Group | v4 E2E | v2.1 E2E | Thay đổi |
|-------|:------:|:--------:|:---------:|
| alarm_calendar | 0.40 | **0.60** | +0.20 |
| contact_call | 1.00 | **1.00** | — |
| map_web_camera | 0.57 | **1.00** | +0.43 ✨ |
| message_email | 0.75 | **1.00** | +0.25 |
| negative_ambiguous | 0.33 | **0.83** | +0.50 ✨ |
| settings_files | 0.80 | **1.00** | +0.20 |

## Các lỗi còn lại (3 lỗi)

Tool selection 30/32=93.8%, chỉ còn 3 lỗi:
1. **alarm_02**: "Mai gọi tôi dậy lúc 7 giờ" → nhầm `send_message` (từ "gọi")
2. **event_01**: Thiếu `EXTRA_EVENT_BEGIN_TIME` → argument accuracy
3. **email_missing_01**: "Gửi email báo cáo giúp tôi" → cần `clarification` nhưng vẫn trả `send_email`

## So sánh với HTTP server (paper)

| Setup | E2E |
|-------|:---:|
| HTTP server (0.5B, colab GPU) | **0.813** |
| On-device v4 (1.5B, phone CPU) | 0.625 |
| **On-device v2.1 (1.5B, eval CPU)** | **0.906** 🔥 |
| On-device v2.1 (1.5B, phone CPU) | 👉 cần benchmark |

## Các file đã tạo/sửa

| File | Mô tả |
|------|-------|
| `prototype/vidroidcall_finetune_colab.ipynb` | Notebook v2.1: epochs=10, warmup=80, lr=3e-4, alpha=16 |
| `prototype/src/evaluate_ft.py` | Sửa base model từ 0.5B → 1.5B |
| `prototype/pipeline_v21.py` | Auto pipeline: evaluate → merge → GGUF → push |
| `prototype/results/model_ft_v21_hybrid_top5_fixconf.jsonl` | Predictions v2.1 |
| `prototype/results/model_ft_v21_hybrid_top5_fixconf_report.json` | Report v2.1 |

## Pipeline còn lại

1. ✅ Fine-tune v2.1 (10 epochs, 128 min Colab)
2. ✅ Evaluate offline (E2E=0.906)
3. ⏳ Merge LoRA → HF model (sẵn merged từ v2)
4. ⏳ Convert GGUF Q4_K_M (sẵn `vidroidcall_v2_q4km.gguf`)
5. ⏳ ADB push lên phone + benchmark on-device