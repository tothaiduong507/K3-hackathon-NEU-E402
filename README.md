# Paper2Venue — AI Research Assistant

Prototype hỗ trợ học viên tìm kiếm, xếp hạng, tổng hợp bài báo khoa học, đọc sâu một paper arXiv và tham khảo conference phù hợp theo phạm vi chủ đề.

> **Lát cắt trung tâm:** Khi một học viên bắt đầu tìm tài liệu cho một chủ đề nghiên cứu, hệ thống lựa chọn những paper đáng đọc trước và tạo bản tổng hợp có dẫn chứng để người dùng quyết định tài liệu cần đọc sâu.

Paper2Venue là công cụ **hỗ trợ quyết định**. Hệ thống không thay người dùng đánh giá chất lượng nghiên cứu, không dự đoán khả năng paper được nhận và không tạo deadline hội nghị.

## Thành viên và phân công

| Thành viên | Mã học viên | Phần phụ trách | Artifact chính |
|---|---|---|---|
| Tô Thái Dương | 2A202601994 | Spec, phạm vi và changelog | `spec.md` |
| Cao Nguyệt Ánh | 2A202601393 | Evidence và impact | `evidence/` |
| Chu Hoàng Việt | 2A202601277 | Prompt, guardrail và eval LLM | `codebase/paper2venue/analyzer.py`, `codebase/paper2venue/deep_summary.py`, `eval/` |
| Trần Vân Anh | 2A202601411 | Search, ranking và API fallback | `semantic_scholar.py`, `arxiv_search.py`, `paper_ranking.py` |
| Bùi Trung Hiếu | 2A202601281 | Streamlit, demo và validation | `codebase/streamlit_app.py`, `validation/`, `demo-slides.pdf` |

Mỗi thành viên chịu trách nhiệm kiểm tra lại artifact của mình và phải giải thích được quyết định thiết kế, cách hoạt động và giới hạn của phần được phân công.

## Tính năng chính

1. **Tìm paper:** ưu tiên Semantic Scholar và tự động chuyển sang arXiv khi nguồn chính bị giới hạn hoặc không khả dụng.
2. **Xếp hạng minh bạch:** sử dụng title overlap, abstract overlap, thứ hạng từ nguồn, citation signal và recency signal; giao diện hiển thị score breakdown.
3. **Smart Literature Review:** phân tích từ 1–5 paper; hỗ trợ cả trường hợp chỉ còn một paper sau lọc.
4. **Deep Paper Summary:** tải và trích xuất PDF arXiv, chia nội dung thành chunk, tóm tắt từng phần rồi tổng hợp thành bản đọc sâu có page reference.
5. **Conference shortlist:** gợi ý venue theo topical fit từ catalog kiểm soát; URL chính thức không lấy từ model.
6. **Export và trace:** kết quả hoàn tất có thể tải dưới dạng JSON/Markdown và được lưu trong `codebase/runs/`.

## Kiến trúc luồng xử lý

```text
Research query
    │
    ▼
Semantic Scholar ── lỗi 403/429/không khả dụng ──► arXiv fallback
    │
    ▼
Chuẩn hóa metadata và áp dụng bộ lọc
    │
    ▼
Transparent paper ranking
    │
    ▼
LLM literature review có structured output và source labels
    │
    ├──► Conference shortlist từ catalog cục bộ
    │
    └──► Deep summary cho một paper arXiv được chọn
```

Các module chính nằm trong `codebase/paper2venue/`:

| Module | Vai trò |
|---|---|
| `semantic_scholar.py` | Semantic Scholar search/exact lookup và chuẩn hóa metadata |
| `arxiv_search.py` | arXiv search, exact-ID lookup và fallback |
| `paper_ranking.py` | Tính relevance score và score breakdown |
| `analyzer.py` | Gọi model để tạo literature review có cấu trúc |
| `arxiv_pdf.py` | Tải và trích xuất text từ PDF arXiv |
| `deep_summary.py` | Chunking, map–reduce summary và kiểm tra page reference |
| `conference_catalog.py` | Tìm venue phù hợp từ catalog kiểm soát |
| `guardrails.py` | Kiểm tra input, phạm vi và các yêu cầu không được hỗ trợ |
| `pipeline.py` | Điều phối flow end-to-end và lưu run log |

## Phần chạy thật và giới hạn

### Chạy thật

- Search paper qua Semantic Scholar/arXiv.
- Heuristic ranking và bộ lọc metadata.
- Lời gọi model thật qua OpenAI hoặc OpenRouter.
- Tải và trích xuất full text từ PDF arXiv có text.
- Structured literature review và deep summary.
- Kiểm tra source label/page reference trước khi render.
- Conference retrieval từ catalog cục bộ.
- Lưu và tải kết quả JSON/Markdown.

### Giới hạn hoặc chưa hỗ trợ

- Semantic Scholar có thể trả 403/429; khi đó hệ thống fallback sang arXiv.
- arXiv không cung cấp citation count, vì vậy nên đặt minimum citations bằng `0` khi dùng fallback.
- Literature review nhiều paper chủ yếu dựa trên abstract; chỉ deep summary đọc PDF arXiv.
- Không hỗ trợ DOI paywall, upload PDF tùy ý, OCR cho PDF scan hoặc đồng bộ thư viện cá nhân.
- Catalog conference có phạm vi giới hạn và không chứa deadline động.
- Conference recommendation chỉ thể hiện topical fit, không phải dự đoán acceptance.
- Công thức, hình và bảng phức tạp có thể không được trích xuất đầy đủ từ PDF.

## Yêu cầu môi trường

- Windows PowerShell
- Python 3.10 trở lên
- Kết nối Internet khi dùng search, tải PDF hoặc gọi model
- Ít nhất một trong hai API key: OpenAI hoặc OpenRouter
- Semantic Scholar API key là tùy chọn

## Cài đặt

Từ thư mục gốc của repo:

```powershell
cd codebase
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `codebase/.env` và điền một model provider:

```dotenv
# Phương án 1: OpenAI
OPENAI_API_KEY=
# OPENAI_MODEL=gpt-4o-mini

# Phương án 2: OpenRouter
# OPENROUTER_API_KEY=
# OPENROUTER_MODEL=openai/gpt-4o-mini
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Tùy chọn
SEMANTIC_SCHOLAR_API_KEY=
```

Không commit `codebase/.env` hoặc API key. File `.env` và `.venv/` đã được ignore.

## Chạy ứng dụng Streamlit

Trong thư mục `codebase/`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Sau khi server khởi động, mở `http://localhost:8501`.

### Luồng demo đề xuất

1. Chọn model provider đã có API key.
2. Nhập một chủ đề cụ thể, ví dụ `retrieval augmented generation for question answering`.
3. Đặt minimum citations về `0` để flow vẫn hoạt động khi fallback sang arXiv.
4. Chọn số paper cần phân tích từ 1–3 để giới hạn thời gian và chi phí.
5. Bấm **Thực thi AI Pipeline**.
6. Giải thích paper ranking bằng score breakdown.
7. Mở literature review và conference shortlist.
8. Chọn một paper arXiv rồi bấm **Đọc và tóm tắt toàn bài**.
9. Chỉ ra PDF coverage, page references và disclaimer.

Failure case phù hợp để demo là Semantic Scholar bị giới hạn và hệ thống chuyển sang arXiv, hoặc citation filter lớn hơn `0` khi nguồn fallback không có citation count.

## Dùng qua dòng lệnh

Trong thư mục `codebase/`:

```powershell
# Tìm paper
.\.venv\Scripts\python.exe -m paper2venue.cli search `
  "retrieval augmented generation" --limit 5

# Xem ranking mà chưa gọi model
.\.venv\Scripts\python.exe -m paper2venue.cli rank `
  "retrieval augmented generation" --limit 10

# Tạo literature review
.\.venv\Scripts\python.exe -m paper2venue.cli review `
  "retrieval augmented generation" --search-limit 10 --analyze-top 3

# Tóm tắt một paper theo arXiv ID
.\.venv\Scripts\python.exe -m paper2venue.cli brief `
  --paper-id "ARXIV:1706.03762"
```

## Kiểm thử và evaluation

Toàn bộ bộ kiểm thử dưới đây không gọi mạng:

```powershell
# Chạy từ thư mục gốc repo
codebase\.venv\Scripts\python.exe eval\run_all_eval.py
```

Hoặc chạy từng phần:

```powershell
cd codebase
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
cd ..
codebase\.venv\Scripts\python.exe eval\run_catalog_eval.py
codebase\.venv\Scripts\python.exe eval\run_ranking_eval.py
```

### Kết quả hiện tại

| Hạng mục | Kết quả | Diễn giải |
|---|---:|---|
| Unit tests | 21/21 | Qua toàn bộ test backend không gọi API ngoài |
| Golden catalog/guardrail | 25/26 — 96,15% | Vượt ngưỡng deterministic 80%; giữ lại 1 case fail |
| Ranking fixtures | 8/8 — 100% | Paper mục tiêu đứng đầu trong 8 fixture |
| Groundedness strict | 11/15 — 73,33% | Chỉ tính claim `SUPPORTED` |
| Groundedness mở rộng | 12/15 — 80,00% | Tính cả `PARTIAL`; phải ghi rõ cách tính |

Deterministic evaluation đã vượt ngưỡng 80%. Tuy nhiên, quality bar trong `spec.md` còn hard condition `≥90%` claim được lấy mẫu có bằng chứng trực tiếp; kết quả groundedness hiện tại **chưa đạt điều kiện này**. Nhóm công bố đầy đủ case chưa đạt thay vì điều chỉnh hoặc loại bỏ chúng.

Case deterministic chưa đạt là `S03_synthetic_metadata_only`: guardrail hiện kiểm tra độ dài input nhưng chưa xác định được một đoạn metadata dài có thực sự chứa nội dung nghiên cứu hay không.

Chi tiết:

- `eval/EVALUATION_REPORT.md`
- `eval/evaluation_summary.json`
- `eval/catalog_eval_results.json`
- `eval/ranking_eval_results.json`
- `eval/groundedness_review.csv`
- `eval/REAL_SOURCE_INDEX.md`

## Guardrail và ranh giới tin cậy

- Output ghi rõ `abstract_only` hoặc `full_text`.
- Source reference chỉ được dùng nếu thuộc tập nhãn nguồn đã cấp cho model.
- Page reference không tồn tại làm lượt phân tích thất bại thay vì được hiển thị.
- URL và metadata conference cuối cùng được resolve từ catalog cục bộ; URL do model tạo bị bỏ qua.
- Không hiển thị deadline chưa được xác minh.
- Không dự đoán acceptance hoặc bảo đảm paper được nhận.
- Khi không đủ nguồn để so sánh nhiều paper, hệ thống chuyển sang single-paper brief.
- Khi không có kết quả sau lọc, hệ thống không gọi model và hướng dẫn người dùng sửa điều kiện.

## Cấu trúc repo

```text
.
├── README.md
├── spec.md
├── demo-slides.pdf
├── codebase/
│   ├── streamlit_app.py
│   ├── paper2venue/
│   ├── data/conferences.json
│   ├── tests/
│   └── runs/
├── evidence/
│   ├── CP1-canvas.docx
│   ├── survey_questions.md
│   ├── survey_responses.csv
│   └── survey_responses.xlsx
├── eval/
│   ├── golden_set.json
│   ├── ranking_cases.json
│   ├── run_all_eval.py
│   └── EVALUATION_REPORT.md
├── validation/
└── reflection/
```

## Evidence, validation và reflection

- `evidence/` lưu Canvas CP1, bộ câu hỏi và phản hồi khảo sát.
- `validation/` lưu feedback log từ các phiên user test, quan sát, quote nguyên văn và thay đổi sau feedback.
- `reflection/` chứa một reflection riêng cho từng thành viên.

Không đưa API key vào evidence, run log, ảnh demo hoặc Git history. Chỉ lưu dữ liệu được phép sử dụng cho Hackathon và ẩn thông tin nhạy cảm trước khi commit lên repo.

## Tài liệu dự án

- `spec.md`: AI Spec và quality bar được chốt trước hạn.
- `01-de-bai.md`: đề bài và tiêu chí nghiệm thu.
- `02-guide.md`: hướng dẫn thực hiện và demo.
- `04-rubric.md`: rubric chấm điểm và checklist artifact.
- `codebase/README.md`: hướng dẫn kỹ thuật chi tiết cho backend.
