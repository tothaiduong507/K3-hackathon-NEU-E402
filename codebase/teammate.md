# Thành viên nhóm Paper2Venue

| Thành viên | Mã học viên | Vai trò chính | Artifact phụ trách |
|---|---|---|---|
| Tô Thái Dương | 2A202601994 | Spec, phạm vi và changelog | `../spec.md` |
| Cao Nguyệt Ánh | 2A202601393 | Evidence và impact | `../evidence/` |
| Chu Hoàng Việt | 2A202601277 | Prompt, guardrail và đánh giá LLM | `paper2venue/analyzer.py`, `paper2venue/deep_summary.py`, `../eval/` |
| Trần Vân Anh | 2A202601411 | Search, ranking và API fallback | `paper2venue/semantic_scholar.py`, `paper2venue/arxiv_search.py`, `paper2venue/paper_ranking.py` |
| Bùi Trung Hiếu | 2A202601281 | Streamlit, demo và validation | `streamlit_app.py`, `../validation/`, `../demo-slides.pdf` |

## Trách nhiệm chung

- Mỗi thành viên kiểm tra và giải thích được phần được phân công.
- Không commit API key, file `.env`, môi trường `.venv/` hoặc dữ liệu nhạy cảm.
- Kết quả eval phải giữ đầy đủ case chưa đạt và được trình bày trung thực.
- Conference recommendation chỉ là topical fit, không phải dự đoán acceptance.
- Khi demo, mỗi thành viên trình bày ít nhất một phần của dự án.
