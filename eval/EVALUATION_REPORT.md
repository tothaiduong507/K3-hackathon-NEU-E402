# Báo cáo đánh giá Paper2Venue

- Thời điểm chạy (UTC): `2026-07-30T18:48:05.743967+00:00`
- Trạng thái: **PASS_DETERMINISTIC_REVIEW_COMPLETED**
- Ngưỡng đạt cho golden/ranking: **80%**

## Kết quả chính

| Hạng mục | Kết quả | Ngưỡng / trạng thái | Kết luận |
|---|---:|---:|---|
| Golden set | 25/26 (96.15%) | ≥ 80% | PASS |
| Ranking | 8/8 (100.00%) | ≥ 80% | PASS |
| Unit tests | 21/21 | Không có test lỗi | PASS |
| Groundedness | 11/15 SUPPORTED (73.33%); SUPPORTED + PARTIAL: 80.00% | Hai người chấm | **COMPLETED** |

## Phạm vi đánh giá

- Golden set đo guardrail và khả năng truy xuất conference từ catalog cục bộ.
- Ranking eval đo việc paper phù hợp có đứng đầu danh sách trong các case cố định.
- Unit tests kiểm tra logic backend bằng mock; không gọi API trực tiếp.
- Ba log deep-summary thật được dùng để chấm groundedness. Trạng thái review hiện tại: `COMPLETED`.

### Golden set theo loại case

| Nhóm | Đạt | Tổng | Tỷ lệ |
|---|---:|---:|---:|
| ambiguity | 4 | 4 | 100.00% |
| domain_specific | 3 | 3 | 100.00% |
| normal | 10 | 10 | 100.00% |
| out_of_scope | 3 | 3 | 100.00% |
| rare | 2 | 2 | 100.00% |
| source_truth | 3 | 4 | 75.00% |

### Golden set theo nguồn

| Nhóm | Đạt | Tổng | Tỷ lệ |
|---|---:|---:|---:|
| real | 11 | 11 | 100.00% |
| synthetic | 14 | 15 | 93.33% |

## Case chưa đạt

- `S03_synthetic_metadata_only`: expected `needs_clarification`, actual `ready`.
  Nguyên nhân: guardrail hiện chỉ kiểm tra độ dài chuỗi nên metadata dài nhưng thiếu nội dung nghiên cứu vẫn được xem là đủ. Case được giữ nguyên để thể hiện giới hạn thật của hệ thống.

## Cách chấm groundedness

1. Mở `eval/groundedness_review.csv`; mỗi người chấm độc lập từng claim bằng `SUPPORTED`, `PARTIAL` hoặc `UNSUPPORTED`.
2. Đối chiếu `source_refs_from_model` với đúng trang PDF trong log tương ứng. Không bắt buộc ghi rater note.
3. Nếu hai người bất đồng, cùng kiểm tra lại và ghi nhãn thống nhất vào `final_status`.
4. Chỉ báo cáo tỷ lệ groundedness sau khi mọi dòng không còn `NOT_REVIEWED`.

Công thức: `groundedness = số claim SUPPORTED / tổng số claim đã chấm`. Có thể báo cáo thêm tỷ lệ `SUPPORTED + PARTIAL`, nhưng phải ghi rõ cách tính.

## Cách chạy lại

Từ thư mục gốc dự án:

```powershell
codebase\.venv\Scripts\python.exe eval\run_all_eval.py
```

Bộ chạy không gọi mạng. Nó chạy unit tests, golden eval, ranking eval và tái tạo toàn bộ artifact tổng hợp.

## Giới hạn cần công bố

- Golden set có 26 case, gồm 11 case lấy từ log chạy thật và 15 case do nhóm thiết kế; đây không phải nhãn do chuyên gia bên ngoài cung cấp.
- Catalog conference là tập cục bộ giới hạn, vì vậy điểm cao không chứng minh độ bao phủ mọi hội nghị.
- Unit/golden/ranking đều là deterministic; chúng không chứng minh bản tóm tắt LLM đúng với toàn văn.
- Groundedness được báo cáo theo hai cách: strict chỉ tính `SUPPORTED`; tỷ lệ mở rộng tính cả `PARTIAL` phải được ghi rõ.

## Artifact

- `eval/evaluation_summary.json`: số liệu tổng hợp máy đọc được.
- `eval/catalog_eval_results.json`: kết quả chi tiết 26 golden cases.
- `eval/ranking_eval_results.json`: kết quả chi tiết 8 ranking cases.
- `eval/unit_test_results.txt`: log unit test.
- `eval/groundedness_review.csv`: 15 claim và nhãn của hai người chấm.
- `eval/REAL_SOURCE_INDEX.md`: ánh xạ 11 case thật về log nguồn.
