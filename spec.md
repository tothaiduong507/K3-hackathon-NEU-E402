# AI SPEC — Smart Literature Review có dẫn chứng · Nhóm NEU Zone A10

**Hướng:** [ ] A — VLearn · [ ] B — Trợ lý Học viên · [x] C — Làn mở

**Loại:** [ ] Tối ưu tính năng có sẵn · [x] Tính năng mới

**Trạng thái:** Draft gần cuối, cập nhật ngày 30/07/2026

**Tên prototype:** Paper2Venue / AI Research Assistant

> **Phạm vi trung tâm:** tìm, xếp hạng và tổng hợp các paper liên quan để hỗ trợ một học viên chốt hướng đọc tiếp. Tóm tắt toàn văn và shortlist conference là các đầu ra hỗ trợ, không phải hai sản phẩm độc lập.

## §1. User & Job

### 1.1 Job executor

**User chính:** một học viên AI20K đang chuẩn bị đề tài nghiên cứu, capstone hoặc bài viết học thuật và cần làm literature review ban đầu.

Các actor rộng hơn trong Canvas CP1 như nghiên cứu sinh, giảng viên và kỹ sư R&D là nhóm người dùng tiềm năng về sau, không phải user chính của lát cắt hiện tại.

### 1.2 Quy trình hiện tại

1. Viết một chủ đề hoặc câu hỏi nghiên cứu.
2. Tìm trên Google Scholar, Semantic Scholar, arXiv hoặc nhiều nguồn khác.
3. Dò tiêu đề, năm, số trích dẫn và đọc lần lượt nhiều abstract.
4. Mở PDF của các paper có vẻ liên quan và tự ghi chú phương pháp, dữ liệu, kết quả, hạn chế.
5. So sánh các ghi chú để xác định paper nền tảng, paper cần đọc trước và khoảng trống có thể nghiên cứu.
6. Khi có ý định công bố, tiếp tục tìm venue phù hợp và tự kiểm tra scope/call for papers trên website chính thức.

### 1.3 Core JTBD

> Khi bắt đầu chốt hướng cho một đề tài nghiên cứu, tôi muốn nhanh chóng xác định những tài liệu đáng đọc trước và hiểu chúng đóng góp gì, khác nhau ở đâu, để dành thời gian đọc sâu đúng tài liệu và ra quyết định về hướng nghiên cứu.

### 1.4 Problem statement

> Học viên phải chuyển qua nhiều nguồn, đọc lặp lại nhiều abstract và tự ghép các ghi chú rời rạc trước khi biết paper nào thực sự liên quan; việc này làm chậm quá trình chốt hướng và tăng nguy cơ bỏ sót hoặc hiểu sai tài liệu quan trọng.

### 1.5 Evidence hiện có và mức tin cậy

Canvas CP1 ghi nhận các giả thuyết sau:

- Người dùng mất khoảng 2-5 **giờ mỗi ngày** để tìm và sàng lọc tài liệu.
- Các hoạt động lặp lại gồm tìm paper, đọc abstract, so sánh paper, lưu thủ công và hiểu nhanh nội dung.
- Mục tiêu kỳ vọng là rút ngắn quá trình khảo sát từ khoảng 2 giờ xuống 15–20 phút.

**Trạng thái:** các con số trên chưa đi kèm bảng trả lời khảo sát, chatlog hoặc phương pháp mining có thể tái hiện, vì vậy **chưa đạt evidence chuẩn A/B và chưa được dùng làm kết luận đo lường**.

### 1.6 Kế hoạch evidence

#### Phương án khảo sát

- Đối tượng: ít nhất 20 người ngoài nhóm đã từng làm bài nghiên cứu, capstone hoặc literature review.
- Điều kiện xác nhận pain: người trả lời chọn mức 4 hoặc 5 cho câu “Việc tìm, sàng lọc và tổng hợp paper làm chậm quá trình chốt hướng nghiên cứu”.
- Log phải lưu: toàn bộ câu hỏi, từng câu trả lời nguyên văn, thời điểm, mã người trả lời; không chỉ ảnh biểu đồ tổng hợp.
- Ngưỡng evidence: `n ≥ 20` và `≥ 50%` xác nhận theo định nghĩa trên.
- File :  `evidence/survey_responses.csv`

### 1.7 Bảng evidence

| Chỉ số                                      | Kết quả | Nguồn kiểm tra                  |
| --------------------------------------------- | --------: | --------------------------------- |
| Số người khảo sát ngoài nhóm           |        23 | `evidence/survey_responses.csv` |
| Số và tỷ lệ xác nhận pain               | 18 / 78% | `evidence/survey_response.csv`   |
|                                               |           |                                   |
| Tỷ lệ yêu cầu có intent thuộc lát cắt |       69% | `evidence/survey_response.csv`   |
| Trung vị thời gian quy trình hiện tại    | 2-5h/lần | survey                            |
|                                               |           |                                   |

Nhóm chỉ thực hiện khảo sát bằng form, hiện tại không có Quote ví dụ.

---

## §2. Impact & quyết định chọn

### 2.1 Công thức so sánh

Mỗi số phải trỏ về một cột trong log evidence. Không dùng các nhãn “rất cao/cao/trung bình” làm bằng chứng thay cho số.

### 2.2 Bảng impact

| Ứng viên                                       | User xác nhận có nhu cầu |     Tần suất |      Tổn thất mỗi lần | Khả thi trong hackathon                                       | Quyết định                  |
| ------------------------------------------------ | ---------------------------: | -------------: | ------------------------: | -------------------------------------------------------------- | ------------------------------ |
| Tìm, xếp hạng và tổng hợp paper liên quan |                   15 người |  17lần/tháng |                2 - 5 giờ | Cao: đã có search, ranking, model summary và export        | **Chọn**                |
| Tóm tắt sâu một paper toàn văn             |                    7 người | 10 lần/tháng |                  10 phút | Trung bình–cao: chạy được với PDF arXiv có text        | Giữ làm chức năng hỗ trợ |
| Gợi ý conference theo scope                    |                    5 người |  5 lần/tháng | 10 phút/rủi ro bỏ lỡ | Trung bình: catalog tĩnh, không có deadline đã xác minh | Giữ shortlist hỗ trợ        |
| Viết Related Work hoàn chỉnh                  |                    1 người |  1 lần/tháng |                  60 phút | Thấp: khó kiểm chứng, rủi ro đạo văn và vượt MVP    | **Loại**                |

### 2.3 Ứng viên bị loại hoặc thu hẹp

- **Viết Related Work tự động:** loại khỏi MVP vì chi phí sai cao, khó đánh giá đúng/sai trong thời gian ngắn và dễ khiến người dùng dùng văn bản chưa kiểm chứng.
- **Theo dõi deadline tự động:** loại khỏi bản hiện tại vì dữ liệu deadline thay đổi và nguồn WikiCFP trong Canvas chưa được xác minh đủ tin cậy. Prototype chỉ cung cấp link chính thức và yêu cầu người dùng tự kiểm tra.
- **Dự đoán khả năng được conference nhận:** ngoài phạm vi; dữ liệu đầu vào không đủ để đưa ra xác suất có trách nhiệm.
- **Tóm tắt mọi PDF bất kỳ:** thu hẹp về PDF arXiv có text; OCR, tài liệu scan và tài liệu paywall chưa được hỗ trợ.

### 2.4 Ứng viên được chọn

**Smart Literature Review có dẫn chứng** được chọn làm lát cắt trung tâm vì nó bao phủ công việc xuất hiện sớm nhất trong workflow và đã có đường chạy end-to-end. Quyết định cuối về impact chỉ được coi là hợp lệ sau khi các cột số ở §2.2 được điền từ §1.

---

## §3. Giải pháp tương tự đã nghiên cứu

| Sản phẩm                                                               | Flow/điểm mạnh quan sát được                                                                           | Điều đáng học                                                                         | Điều cần tránh                                                           | Prototype khác gì                                                                                        |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| [Semantic Scholar](https://www.semanticscholar.org/product)               | Tìm kiếm paper, filter, TLDR, citation, library và research feed                                           | Cho người dùng thấy metadata, link nguồn và tín hiệu citation ngay tại danh sách | Không coi một TLDR siêu ngắn là đủ cho literature review              | Gom ranking, tổng hợp nhiều paper, deep summary và venue shortlist trong một flow demo                |
| [NotebookLM](https://support.google.com/notebooklm/answer/16164461?hl=en) | Trả lời/tổng hợp dựa trên nguồn người dùng cung cấp, có citation nội tuyến                      | Ground câu trả lời vào nguồn và cho phép kiểm tra vị trí bằng chứng            | Không trình bày nội dung không có căn cứ như kết luận chắc chắn | Tự tìm nguồn từ chủ đề trước, sau đó mới tổng hợp; full-text chỉ dùng khi lấy được PDF |
| [Connected Papers](https://www.connectedpapers.com/about)                 | Bắt đầu từ một paper và dựng đồ thị các paper tương tự bằng co-citation/bibliographic coupling | Cung cấp cách khám phá paper lân cận và prior/derivative work                       | Không dùng một “điểm liên quan” mơ hồ mà thiếu giải thích      | Bắt đầu từ research query và hiển thị breakdown của điểm xếp hạng                              |

**Kết luận thiết kế:** giá trị khác biệt của prototype không nằm ở việc thay thế các công cụ trên, mà ở flow ngắn từ `chủ đề → shortlist có lý do → tổng hợp có mức bằng chứng → đọc sâu → venue theo scope`, kèm hành vi fallback và giới hạn rõ ràng.

---

## §4. Thiết kế

### 4.1 Lát cắt một câu

> Với một học viên AI20K đang chốt hướng cho đề tài nghiên cứu, hệ thống quyết định những paper nào đáng đọc trước và tạo một bản tổng hợp có dẫn chứng để học viên chọn tài liệu cần đọc sâu tiếp theo.

| Thành phần               | Nội dung                                                        |
| -------------------------- | ---------------------------------------------------------------- |
| 1 user                     | Một học viên AI20K đang chốt hướng nghiên cứu           |
| 1 việc                    | Sàng lọc literature ban đầu cho một chủ đề               |
| 1 quyết định trung tâm | Paper nào đáng đọc trước                                  |
| 1 kết quả                | Bản tổng hợp có dẫn chứng để chọn tài liệu đọc sâu |

### 4.2 Non-goals

Prototype **không**:

1. Dự đoán xác suất paper được nhận tại conference.
2. Tự tạo hoặc cam kết deadline conference.
3. Viết Related Work hoàn chỉnh để người dùng nộp.
4. Thay thế việc đọc paper gốc hoặc quyết định học thuật của người dùng.
5. Tóm tắt nội dung toàn văn khi chỉ có abstract nhưng gắn nhãn như đã đọc cả bài.
6. Hỗ trợ OCR chính xác cho PDF scan, công thức, hình và bảng phức tạp.
7. Bảo đảm tìm được mọi paper quan trọng từ một truy vấn ngắn hoặc mơ hồ.

### 4.3 Mức prototype

**[x] Working** · [ ] Mock · [ ] Sketch

#### Phần chạy thật

- Streamlit nhận research query, năm, citation tối thiểu, số paper cần phân tích và ngôn ngữ.
- Tìm paper qua Semantic Scholar; tự chuyển sang arXiv khi nguồn chính bị chặn/rate-limit.
- Xếp hạng minh bạch bằng title overlap, abstract overlap, thứ hạng nguồn, citation signal và recency signal.
- Gọi model thật để tạo literature review từ abstract của 1–5 paper.
- Nếu chỉ còn một paper, tạo single-paper brief và không suy diễn so sánh chéo.
- Tải và trích xuất PDF arXiv để tạo deep summary hai lượt, có tham chiếu trang hợp lệ.
- Gợi ý shortlist conference từ catalog có kiểm soát; URL cuối được lấy từ catalog, không lấy từ model.
- Lưu và cho tải kết quả JSON/Markdown; deep summary có cache.

#### Phần giới hạn hoặc chưa có

- Semantic Scholar key đã trả 403 trong lần kiểm tra ngày 30/07/2026; anonymous request có thể bị rate-limit. Flow fallback arXiv là thật nhưng thiếu citation count.
- Conference catalog là dữ liệu tĩnh do nhóm kiểm soát; chưa phải hệ thống cập nhật CFP/deadline.
- Literature review nhiều paper chỉ dựa trên abstract; chỉ màn hình “Đọc và tóm tắt toàn bài” dùng text PDF.
- Không hỗ trợ upload PDF tùy ý, DOI paywall, OCR hoặc đồng bộ thư viện cá nhân.
- Chưa có evidence người dùng, validation log và lượt chấm chất lượng đầy đủ cho output của model.

### 4.4 Automation và cost of error

**Chọn:** [x] Augment · [x] Conditional · [ ] Automate

- Hệ thống tự động tìm, tính điểm, tạo tóm tắt và shortlist.
- Người dùng vẫn chọn query, filter, số paper, paper cần đọc sâu và quyết định học thuật cuối cùng.
- Khi thiếu full text, thiếu citation hoặc nguồn chính lỗi, hệ thống hạ mức bằng chứng/fallback thay vì giả vờ có dữ liệu.
- Cost of error ở mức đáng kể: xếp hạng sai có thể khiến user bỏ qua paper nền tảng; tóm tắt sai có thể làm lệch hướng nghiên cứu; venue sai có thể làm mất thời gian chuẩn bị bài. Vì vậy không tự động nộp, không dự đoán acceptance và luôn để người dùng kiểm tra nguồn.

### 4.5 Nguyên tắc HAX/PAIR đã áp dụng

| Nguyên tắc                                               | Áp cụ thể trong prototype                                                                                                                                            | Cách kiểm chứng                                                                              |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **G1 — Làm rõ hệ thống có thể làm gì**      | Màn hình đầu mô tả pipeline tìm, tóm tắt và gợi ý conference; nút chạy ghi rõ “Thực thi AI Pipeline”                                                  | User mới nói lại đúng ba khả năng chính                                                 |
| **G2 — Làm rõ hệ thống làm tốt đến đâu**  | Hiển thị`abstract_only`/`full_text`, trạng thái Semantic Scholar → arXiv, citation `N/A`, confidence và disclaimer                                          | Case fallback không được hiểu nhầm là có dữ liệu citation/full text                   |
| **G8 — Gạt bỏ dễ dàng**                         | Gợi ý của hệ thống không chặn flow: user có thể bỏ qua một paper/venue, quay lại danh sách và chọn nguồn khác; export không thay đổi dữ liệu gốc | Bỏ qua một gợi ý và tiếp tục task mà không cần xác nhận hoặc khởi động lại app |
| **G9 — Hỗ trợ sửa lỗi hiệu quả**              | Query, năm, citation tối thiểu và số paper đều sửa được; khi arXiv không có citation app nhắc đặt citation về 0                                        | Case zero-result có chỉ dẫn sửa đúng biến gây lỗi                                      |
| **G10 — Thu hẹp phạm vi khi không chắc chắn**  | Một paper chỉ tạo brief; không có arXiv ID thì tắt/không thực hiện deep summary; API lỗi thì fallback hoặc báo lỗi                                       | Không sinh so sánh chéo từ một nguồn và không giả full text                            |
| **G11 — Giải thích vì sao hệ thống làm vậy** | Mỗi paper có điểm`/100`, từ khóa khớp và score breakdown; conference có fit reason; deep summary có page refs                                               | Người dùng chỉ ra được lý do một kết quả được xếp trên kết quả khác          |
| **G17 — Quyền kiểm soát tổng**                  | User chọn filter, số paper phân tích (1–5), ngôn ngữ và paper cần đọc sâu                                                                                   | User có thể giảm chi phí model hoặc chỉ phân tích một paper                            |
| **PAIR — Graceful failure**                         | Nguồn chính lỗi chuyển sang arXiv, thiếu full text trả`full_text_unavailable`, deadline không xác minh thì không hiển thị                                 | Các case lỗi kết thúc bằng trạng thái có thể hành động, không crash                |

---

## §5. Kiểu lỗi — 4 lớp chỗ khó và kịch bản

Taxonomy:

- **① Source/ground truth:** nguồn thiếu, sai hoặc model nói vượt nguồn.
- **② Ambiguity/low confidence:** yêu cầu mơ hồ hoặc bằng chứng quá ít.
- **③ Out of scope/unsafe delegation:** người dùng đòi quyết định mà hệ thống không nên đưa.
- **④ Domain-specific:** đặc thù paper/PDF/conference làm flow chung không đủ.

| ID  | Lớp  | Input/tình huống                                                             | Rủi ro                                                 | Hành vi mong muốn                                                                                                        | Nguyên tắc áp | Trạng thái build                                 |
| --- | ----- | ------------------------------------------------------------------------------ | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------- | -------------------------------------------------- |
| R01 | ①    | Model tạo claim không có trong abstract/PDF                                 | Người dùng tin nhầm                                 | Chỉ chấp nhận source ref nằm trong nhãn đã cấp; hiển thị mức bằng chứng và yêu cầu kiểm tra paper gốc    | G2, G11          | Có guardrail nhãn nguồn; cần eval groundedness |
| R02 | ①    | Model tạo URL/deadline conference                                             | Thông tin không tồn tại hoặc đã cũ              | Bỏ URL do model tạo, resolve URL từ catalog; không hiển thị deadline chưa xác minh                                 | G10, PAIR        | Đã có                                           |
| R03 | ①    | Semantic Scholar trả 403/429                                                  | Search dừng                                            | Tự chuyển sang arXiv và thông báo citation count không khả dụng                                                    | G10, PAIR        | Đã có                                           |
| R04 | ②    | Query “attention” quá rộng                                                 | Paper nền tảng bị chìm hoặc kết quả lệch intent | Hiển thị tín hiệu khớp/điểm, cho sửa query/title; không khẳng định danh sách là đầy đủ                   | G2, G9, G11      | Có correction; chưa có bước hỏi làm rõ     |
| R05 | ②    | Sau filter chỉ còn 1 paper                                                   | Model bịa điểm chung/khác biệt                     | Tạo single-paper brief, ghi rõ không đủ nguồn để so sánh chéo                                                    | G10              | Đã có                                           |
| R06 | ②    | arXiv fallback không có citation count nhưng min citation > 0               | Loại hết kết quả hợp lệ                           | Báo lý do và gợi ý đặt min citation về 0                                                                           | G9, G10          | Đã có                                           |
| R07 | ③    | “Hãy bảo đảm paper được nhận” hoặc yêu cầu acceptance probability | Ủy quyền quyết định không có căn cứ            | Từ chối dự đoán; chỉ trả shortlist theo scope và link kiểm tra                                                    | G1, G10          | Có ở guardrail/backend                           |
| R08 | ③    | “Tự viết Related Work và tạo citation còn thiếu”                       | Đạo văn/fabricated citation                          | Không tạo citation/paper mới; chỉ tổng hợp nguồn đã truy xuất                                                    | G1, G10          | Có nguyên tắc; cần test UI trực tiếp         |
| R09 | ④    | Paper không có arXiv ID/PDF mở                                              | Không thể đọc toàn văn                            | Vô hiệu hóa deep summary hoặc trả`full_text_unavailable`; vẫn cho brief từ abstract                               | G2, G10, PAIR    | Đã có                                           |
| R10 | ④    | PDF scan, công thức, hình hoặc bảng phức tạp                            | Trích xuất text thiếu/sai                            | Cảnh báo hạn chế, giữ page refs, yêu cầu kiểm tra hình/bảng gốc                                                 | G2, G11          | Đã có disclaimer; chưa có OCR                 |
| R11 | ④    | PDF dài hơn giới hạn                                                       | Cắt mất phần quan trọng/chi phí lớn               | Giới hạn tối đa 80 trang và 400.000 ký tự, báo coverage thực tế                                                  | G2, G10          | Đã có                                           |
| R12 | ①/④ | Scope conference trong catalog đã cũ                                        | Gợi ý venue sai                                       | Hiển thị URL chính thức và yêu cầu user xác minh CFP hiện tại; không dùng deadline catalog không kiểm chứng | G2, G11          | Một phần; cần quy trình cập nhật catalog     |

---

## §6. Bốn đường đi của trải nghiệm

### 6.1 Happy path

1. User nhập một chủ đề đủ cụ thể, chọn năm và citation tối thiểu.
2. App tìm paper, xếp hạng và hiển thị tiến trình.
3. Model tổng hợp top paper từ abstract, nêu đóng góp, điểm chung/khác và research gaps.
4. App hiển thị shortlist conference theo scope với link chính thức.
5. User chọn một paper có arXiv ID để đọc và tóm tắt toàn bài.
6. App tải PDF, trích xuất text, tóm tắt theo section rồi tổng hợp; user tải Markdown/JSON.

### 6.2 Low-confidence path ②

- Nếu chỉ có một paper đủ điều kiện: tạo single-paper brief, không sinh kết luận so sánh.
- Nếu dùng arXiv fallback: hiển thị cảnh báo nguồn, citation `N/A` và không dùng citation như bằng chứng xếp hạng.
- Nếu query rộng: hiển thị breakdown để user tự nhận ra khớp yếu và sửa query/title.
- Nếu source level là `abstract_only`: ghi rõ tóm tắt chưa đại diện cho toàn văn.

### 6.3 Failure/không có căn cứ ①

- Không có kết quả sau filter: không gọi model; báo điều kiện nào có thể đã loại kết quả và gợi ý sửa.
- Semantic Scholar lỗi: fallback arXiv; nếu cả hai lỗi thì trả lỗi có thông tin, không hiển thị dữ liệu cũ như kết quả mới.
- Không lấy được PDF/text: trả `full_text_unavailable`, giữ khả năng xem nguồn/brief abstract.
- Model trả JSON sai hoặc request lỗi: hiển thị lỗi và cho chạy lại; không render output dở dang như hoàn tất.

### 6.4 Correction path

- User sửa query bằng title đầy đủ, thêm thuật ngữ cụ thể, đổi năm hoặc đặt citation tối thiểu về 0.
- User đổi số paper phân tích từ 1 đến 5 rồi chạy lại.
- User quay lại từ deep summary để chọn paper khác.
- User mở link paper/trang conference chính thức để đối chiếu và dùng export làm bản nháp ghi chú, không làm nguồn trích dẫn thay paper gốc.

### 6.5 Khi bị đòi ngoài phạm vi ③

Hệ thống không dự đoán acceptance, không tạo deadline/citation, không tự nộp bài và không tuyên bố đã đọc full text khi chỉ có abstract. Câu trả lời thay thế là shortlist theo scope, nguồn kiểm tra và giới hạn bằng chứng.

### 6.6 Case đặc thù domain ④

Với PDF scan/công thức/bảng, paper không mở, paper quá dài hoặc venue thay đổi scope, hệ thống phải nêu rõ phần chưa đọc/không xác minh và chuyển quyền quyết định về người dùng.

---

## §7. Kiểm thử

### 7.1 Quyết định trung tâm cần đo

Đầu vào là một research query và tập paper ứng viên; đầu ra cần đánh giá là **paper nào được ưu tiên đọc và bản tổng hợp có đủ căn cứ để user kiểm tra hay không**.

### 7.2 Chiều chất lượng và định nghĩa kiểm chứng được

| Chiều                      | Định nghĩa pass cho một case                                                                                                                          | Cách chấm                                                             |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Retrieval/ranking relevance | Ít nhất một paper trong`expected_paper_ids` nằm trong top 3; nếu case có thứ tự bắt buộc thì paper mục tiêu đứng trước distractor      | Script đối chiếu ID, không chấm cảm tính                         |
| Evidence-reference validity | 100%`source_refs` xuất hiện trong tập nhãn nguồn đã cấp (`abstract`, `p.n`)                                                                 | Script kiểm tra tập hợp                                              |
| Claim groundedness          | Mỗi claim chính được rater chỉ ra câu/đoạn hoặc trang hỗ trợ; không tìm thấy bằng chứng thì fail claim                                  | Hai người ngoài nhóm chấm độc lập 5 claim/case, lưu quote/page |
| Summary coverage            | Các trường bắt buộc phù hợp nguồn không rỗng: problem, contribution, method, findings, limitations; full text có section summary và page refs | Script schema + manual review                                           |
| Source-level honesty        | Abstract-only không chứa nhãn/trình bày như full-text; full-text ghi coverage và disclaimer                                                        | Script kiểm tra cờ + ảnh UI                                          |
| Conference scope fit        | Venue mong đợi nằm trong top 3 và fit reason có ít nhất một topic từ catalog; URL đúng tuyệt đối với catalog                               | Script deterministic                                                    |
| Graceful failure            | Status/message đúng với expected behavior và không gọi bước model không cần thiết                                                              | Unit/integration test                                                   |
| Boundary safety             | Không có acceptance probability, deadline chưa xác minh, paper/citation/URL tự tạo                                                                  | Exact-match/regex + manual audit                                        |

### 7.3 Golden set

#### Hiện có

- `eval/golden_set.json`: 20 case tổng hợp cho routing, guardrail và conference catalog.
- Cơ cấu: 8 normal, 2 source truth, 2 ambiguity, 2 out of scope, 2 domain specific, 4 rare.
- `eval/ranking_cases.json`: 8 fixture ranking deterministic.

#### Cơ cấu bản cuối

| Nhóm case               | Số case tối thiểu | Yêu cầu                                                      |
| ------------------------ | -------------------: | -------------------------------------------------------------- |
| Normal                   |                8–10 | Chủ đề đủ cụ thể, có paper liên quan                  |
| Source/ground truth      |                  ≥2 | Claim/URL/deadline/citation không có nguồn                  |
| Ambiguity/low confidence |                  ≥2 | Query rộng, một paper, filter quá chặt                     |
| Out of scope             |                  ≥2 | Acceptance, tự tạo citation/Related Work                     |
| Domain specific          |                  ≥2 | PDF scan/paywall/dài/bảng-công thức                        |
| Rare                     |                 2–4 | API failure, malformed model output, Unicode/title đặc biệt |
| Case từ yêu cầu thật |                 ≥10 | Giữ nguyên câu chữ sau khi ẩn thông tin nhạy cảm       |

### 7.4 Quality bar

> **Quality bar được chốt để freeze trong commit spec:** Đạt khi **≥80% tổng số case qua toàn bộ chiều áp dụng**, đồng thời thỏa các hard condition: **0 URL paper/conference hoặc deadline bị bịa; 0 dự đoán acceptance; 100% source reference hợp lệ; ≥90% claim được lấy mẫu có bằng chứng trực tiếp**.

Ghi chú:

- Quality bar này khớp ngưỡng 0,80 đang có trong `eval/golden_set.json`.
- Nhóm phải xác nhận và commit bar trước hạn cứng của chương trình; không sửa bar sau khi nhìn kết quả để làm đẹp điểm.
- Nếu không đạt, vẫn lưu toàn bộ case fail và phân tích nguyên nhân.

### 7.5 Kết quả hiện có

| Lượt chạy                                   | Phạm vi                                           |                        Kết quả | So với bar           | Hạn chế                             |
| ---------------------------------------------- | -------------------------------------------------- | -------------------------------: | --------------------- | ------------------------------------- |
| `catalog_eval_results.json`                  | Guardrail + conference catalog, 20 case tổng hợp |                     20/20 = 100% | Qua bar deterministic | Không đo chất lượng LLM summary  |
| `ranking_eval_results.json`                  | Ranking fixture                                    |                       8/8 = 100% | Qua bar deterministic | Không phải live retrieval           |
| Unit tests backend                             | 21 test không gọi API ngoài                     |                            21/21 | Qua                   | Cần commit log test để phúc khảo |
| Live deep summary — Attention Is All You Need | PDF arXiv, model`gpt-4o-mini`                    | Completed, 15/15 trang, 4 chunks | Chưa kết luận      | Chưa chấm groundedness thủ công   |
| Live deep summary — Visual Attention Network  | PDF arXiv, model`gpt-4o-mini`                    | Completed, 12/12 trang, 5 chunks | Chưa kết luận      | Chưa chấm groundedness thủ công   |
| Live deep summary — External Attention        | PDF arXiv, model`gpt-4o-mini`                    | Completed, 11/11 trang, 4 chunks | Chưa kết luận      | Chưa chấm groundedness thủ công   |

### 7.6 Case fail đã biết

| Case                                                      | Quan sát                                           | Nguyên nhân giả thuyết                                                                                                                     | Hành động/đo lại                                                                        |
| --------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Query`attention`, năm từ 2016, citation tối thiểu 0 | Có lúc không thấy “Attention Is All You Need” | Query quá rộng; arXiv search/ranking ưu tiên khớp và thứ tự nguồn, không đảm bảo recall của paper người dùng ngầm nghĩ tới | Thêm case live retrieval; thử title đầy đủ và query cụ thể; đo target có ở top 3 |
| Semantic Scholar exact/search                             | Key trả 403; request công khai có thể 429       | Quyền key/rate limit phía nguồn                                                                                                             | Lưu raw status đã ẩn key; xác nhận fallback arXiv                                      |
| arXiv fallback + citation filter > 0                      | Không còn paper                                   | arXiv không trả citation count                                                                                                               | Expected behavior: cảnh báo và yêu cầu đặt 0                                          |

### 7.7 Lượt kiểm thử bắt buộc tiếp theo

1. Thu ít nhất 10 query thật và đóng băng expected behavior trước khi chạy.
2. Mở rộng golden set để mọi case đi qua quyết định trung tâm của model khi phù hợp.
3. Chạy trọn bộ một lượt, không xóa case fail; lưu JSON kết quả và bản tổng hợp phần trăm.
4. Hai người chấm độc lập claim groundedness; lưu chênh lệch và cách phân xử.
5. Chạy lại sau mỗi thay đổi prompt/code; không thay quality bar.

---

## §8. Phân công & kế hoạch

### 8.1 Phân công có tên

| Thành viên      | Mã học viên | Phần chịu trách nhiệm     | Artifact phải giải thích được                                  |
| ----------------- | -------------- | ----------------------------- | -------------------------------------------------------------------- |
| Tô Thái Dương | 2A202601994    | Spec, scope, changelog        | `spec.md`                                                          |
| Cao Nguyệt Ánh  | 2A202601393    | Evidence và impact           | `evidence/`                                                        |
| Chu Hoàng Việt  | 2A202601277    | Prompt, guardrail, eval LLM   | `codebase/paper2venue/analyzer.py`, `deep_summary.py`, `eval/` |
| Trần Vân Anh    | 2A202601411    | Search, ranking, API/fallback | `semantic_scholar.py`, `arxiv_search.py`, `paper_ranking.py`   |
| Bùi Trung Hiếu  | 2A202601281    | Streamlit, demo, validation   | `streamlit_app.py`, `validation/`, `slides/`                   |

### 8.2 Willing users và validation CP5

| Người dùng           | Vai trò                               | Đã đồng ý?                             | Kịch bản sẽ test                              | Người log       |
| ----------------------- | -------------------------------------- | ------------------------------------------- | ------------------------------------------------ | ----------------- |
| Nguyễn Quốc Anh       | Sinh viên đã từng làm NCK         | Có — xác nhận ngày 30/07 qua Messenger | Tìm paper cho chủ đề thật                   | Tô Thái Dương |
| Đặng Văn Nhân       | Sinh viên đã từng làm NCK         | Có — xác nhận ngày 30/07 qua Messenger | Chọn một paper và kiểm tra deep summary      | Tô Thái Dương |
| Nguyễn Hữu Hoàng Anh | Sinh viên từng làm capstone project | Có — xác nhận ngày 30/07 qua Zalo      | Sửa query khi kết quả không đúng kỳ vọng | Tô Thái Dương |

### 8.4 Kế hoạch hoàn thiện

| Ưu tiên | Việc                         | Definition of done                                                                                       |
| --------- | ----------------------------- | -------------------------------------------------------------------------------------------------------- |
| P0        | Evidence A/B                  | Log gốc + summary + ≥5 quote + impact có số                                                          |
| P0        | Golden set thật              | ≥20 case đúng cơ cấu, ≥10 query thật                                                              |
| P0        | Eval quyết định trung tâm | Một lượt đầy đủ, có case fail, % so với bar                                                     |
| P0        | Validation                    | ≥5 người, quote/tên/vai trò, ≥1 thay đổi ghi changelog                                           |
| P1        | Repo hygiene                  | README có tên phân công; không commit`.env`, `.venv` hoặc key                                  |
| P1        | Demo                          | Slide 6 trang, case happy + case fail live, dry run 5 phút                                              |
| P1        | Reflection                    | Mỗi thành viên viết vai trò, phần làm, cách dùng công cụ hỗ trợ và bài học từ case fail |

---

## §9. Changelog

| Thời điểm | Đổi gì                                                                                          | Vì sao / feedback hoặc case                                                                  |
| ------------ | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| CP1          | Chọn Smart Literature Review từ ba cơ hội: tìm paper, conference recommendation, Related Work | Canvas đánh giá search có tần suất cao và khả thi nhất; số impact vẫn cần evidence |
| 30/07/2026   | Thêm Semantic Scholar → arXiv fallback                                                           | Semantic Scholar trả 403/429 trong kiểm tra                                                  |
| 30/07/2026   | Citation tối thiểu có cảnh báo khi dùng arXiv                                                | arXiv không cung cấp citation count                                                          |
| 30/07/2026   | Hỗ trợ phân tích từ 1 paper                                                                   | Tránh flow hỏng khi filter chỉ để lại một paper; không suy diễn so sánh chéo        |
| 30/07/2026   | Thêm deep paper summary từ PDF arXiv                                                             | User cần tóm tắt cụ thể cả bài thay vì TLDR từ abstract                               |
| 30/07/2026   | Không hiển thị deadline hoặc acceptance probability                                            | Nguồn deadline chưa được xác minh, cost of error cao                                     |
|              |                                                                                                    |                                                                                                |

---
