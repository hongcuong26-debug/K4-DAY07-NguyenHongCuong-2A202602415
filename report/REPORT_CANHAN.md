# Báo cáo cá nhân — Lab 07

**Họ tên:** Nguyễn Hồng Cường — **MSSV:** 2A202602415
**Lớp:** K4-L3B — **Nhóm:** Đạt – Cường – Trang
**Ngày thực hiện:** 20/09/2026 — **Vai trò:** R2, thiết kế benchmark
**Chiến lược riêng:** RecursiveChunker, chunk_size=500, không overlap.

Code và bản báo cáo được hoàn thiện với hỗ trợ AI. Các số liệu bên dưới được chạy
trong repo này; không coi đó là bằng chứng Đạt hoặc Trang đã tự chạy bài cá nhân.

## 1. Khởi động

Cosine similarity đo góc giữa hai vector. Giá trị cao cho biết chúng hướng gần nhau;
với embedding ngữ nghĩa tốt, thường tương ứng nội dung gần nghĩa. Giá trị nằm trong
[-1, 1]; giá trị 0 có thể là trực giao, không tự động có nghĩa văn bản vô nghĩa.

Ví dụ cao: “Tôi muốn gửi lại món hàng vì bị hỏng.” và “Sản phẩm lỗi nên tôi đề nghị
lấy lại tiền.” Hai câu dùng cách diễn đạt khác nhưng cùng ý định xử lý món hàng lỗi.
Ví dụ thấp: “Hạn gửi yêu cầu là mười lăm ngày.” và “Tối nay tôi đi xem phim.”

Cosine bỏ ảnh hưởng độ lớn vector, tập trung vào hướng nên hữu ích khi độ lớn không
phản ánh ý nghĩa. Với vector đã chuẩn hóa, khoảng cách Euclid và cosine cho cùng
thứ tự: squared_distance = 2 - 2*cosine; không nên nói cosine luôn tốt hơn Euclid.

- Overlap 50: ceil((10000 - 50)/(500 - 50)) = ceil(9950/450) = **23 chunk**.
- Overlap 100: ceil(9900/400) = **25 chunk**, tăng 2 chunk.
- Chạy FixedSizeChunker xác nhận: {'50': 23, '100': 25}. Overlap lớn giúp giữ câu/điều
  kiện nằm sát ranh giới, đổi lại tốn embedding, bộ nhớ và dễ lấy kết quả trùng lặp.

## 2. Hướng tiếp cận

**SentenceChunker:** dùng `(?<=[.!?])\s+`, tách ở khoảng trắng sau dấu kết câu nên
giữ dấu câu, strip mỗi câu rồi gom tối đa N câu. Rỗng trả `[]`. Regex chưa nhận biết
`TS.`, `v.v.` hoặc dấu kết câu bên trong trích dẫn. Số `3.14` không bị tách vì không
có khoảng trắng; dạng `3. 14`, đánh số danh sách hoặc số bị xuống dòng có thể bị
nhầm là hai câu. Đây không phải bộ phân tích câu tiếng Việt đầy đủ.

**RecursiveChunker:** ưu tiên đoạn, dòng, câu, từ rồi ký tự. Đệ quy mảnh quá dài với
separator còn lại, gom mảnh liền nhau tới giới hạn. Giữ delimiter nên nối mọi chunk
sẽ khôi phục đúng văn bản. Ba base case là rỗng; đã vừa kích thước; hết separator
hoặc gặp separator rỗng thì cắt cứng. Không có overlap nên một thông tin vẫn có thể
bị tách khỏi điều kiện, và chunk sau không tự lặp tiêu đề.

**Store:** dùng list in-memory, bỏ rẽ nhánh Chroma. Mỗi Document tạo một record,
không tự chunk. Copy sâu metadata, giữ doc_id đã cung cấp; nếu thiếu thì suy ra file
từ phần trước `#` của id. Vectors trong lab chuẩn hóa nên search xếp theo dot product;
`compute_similarity` vẫn tính đủ cosine và xử lý vector 0.

**Filter và delete:** lọc tất cả điều kiện metadata trước khi xếp hạng bằng cùng
`_search_records`. Nếu lọc sau top-k, các slot có thể đã bị tài liệu sai đối tượng
chiếm hết. Delete loại toàn bộ chunk có doc_id gốc khớp, trả bool theo số bản ghi giảm.
Kết quả search không chứa vector và không chia sẻ metadata có thể sửa với store.

**Agent:** lấy top-k, đánh số [1]… kèm source_url và chunk id, đưa vào prompt với
yêu cầu chỉ dùng chứng cứ và trích dẫn nguồn. Rỗng không gọi llm_fn. Chữ ký answer
giữ nguyên; benchmark dùng FilteredView để áp dụng filter trước retrieval của agent.
Prompt giảm nguy cơ bịa, không chứng minh LLM luôn tuân thủ. Trong benchmark,
llm_fn là bộ chọn đoạn theo giao từ vựng, **không phải LLM sinh câu trả lời**.

## 3. Hoàn thiện code

**42/42 passed**, không sửa `tests/test_solution.py`, không còn TODO/NotImplementedError
trong src. Python thực tế 3.12.3 (đề cho phép 3.10+), pytest 9.1.1, Windows.
Output gốc: [pytest_output.txt](pytest_output.txt). Kiểm tra bổ sung:
[validation_output.txt](validation_output.txt); demo: [main_output.txt](main_output.txt).

```text
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Nguyen Hong Cuong\K4-DAY07-NguyenHongCuong-2A202602415\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Nguyen Hong Cuong\K4-DAY07-NguyenHongCuong-2A202602415
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.28s ==============================
```

## 4. Dự đoán độ tương tự

Backend: **MockEmbedder, MD5, 64 chiều**. Dự đoán là về nghĩa câu; số đo thật là
mock nên không dùng để kết luận model hiểu nghĩa. Quy ước minh họa: cao >= 0.7,
thấp <= 0.3, còn lại trung bình; đây không phải ngưỡng được hiệu chuẩn cho hệ thật.

| # | Câu A | Câu B | Dự đoán | Cosine thực đo | Đúng nhãn? |
|---|---|---|---|---|---|
| 1 | Tôi muốn gửi lại món hàng vì bị hỏng. | Sản phẩm lỗi nên tôi đề nghị lấy lại tiền. | cao | -0.071474 | Không |
| 2 | Tiền được chuyển lại về thẻ đã thanh toán. | Khoản hoàn trả đi vào tài khoản thẻ dùng lúc mua. | cao | 0.147692 | Không |
| 3 | Hạn gửi yêu cầu là mười lăm ngày. | Tối nay tôi đi xem phim. | thấp | -0.089533 | Trùng nhãn; không chứng minh ngữ nghĩa |
| 4 | Người bán phải phản hồi khiếu nại đúng hạn. | Một tam giác có ba cạnh. | thấp | 0.059367 | Trùng nhãn; không chứng minh ngữ nghĩa |
| 5 | Bạn cần quay video khi mở kiện hàng. | Hãy ghi hình lúc bóc gói để có bằng chứng. | cao | 0.005172 | Không |

Bất ngờ là các cặp diễn đạt tương đương vẫn có điểm thấp. Nguyên nhân đã biết:
mock băm chuỗi rồi sinh vector, không học nghĩa. Cặp thấp có điểm thấp cũng chỉ là
sự trùng hợp trong thí nghiệm này. Muốn đánh giá ngữ nghĩa cần chạy lại model đa ngữ.

## 5. Kết quả truy xuất riêng

Chạy `python bench.py` (mặc định recursive), backend **mock:md5-64-v1**;
thời điểm UTC 2026-09-20T03:16:04.488002+00:00. Chỉ dùng corpus Shopee, không trộn dữ liệu mẫu.
Nạp **11 chunk**, trung bình **363.82 ký tự**.

| # | Câu hỏi | Top-3: chunk (cosine) | Hạng có đủ đáp án | Điểm nội dung /2 |
|---|---|---|---|---|
| Q1 | Tự sắp xếp gửi trả hàng thì tôi có phải trả phí vận chuyển không? | seller-phan-hoi#1 (0.1759); seller-phan-hoi#0 (-0.0091) | 1 | 2 |
| Q2 | Thực phẩm tươi sống hoặc đông lạnh có thời hạn yêu cầu trả hàng bao lâu và ngoại lệ nào? | buyer-nhan-tien#1 (0.1340); buyer-gui-yeu-cau#1 (0.1037); seller-phan-hoi#1 (0.0546) | Không có | 0 |
| Q3 | Biểu mẫu tạo yêu cầu trả hàng cần điền thông tin và bằng chứng gì trước khi gửi? | buyer-nhan-tien#0 (0.2060); buyer-gui-hang#0 (0.1566); buyer-dieu-kien#1 (0.1321) | Không có | 0 |
| Q4 | Liệt kê ba hình thức gửi hàng hoàn trả và hình thức nào miễn phí cho người mua? | buyer-dieu-kien#0 (0.1764); buyer-dieu-kien#1 (0.1426); buyer-gui-hang#0 (0.0815) | 3 | 1 |
| Q5 | Thanh toán bằng thẻ tín dụng hoặc ghi nợ thì tiền hoàn về đâu, sau bao lâu kể từ khi được duyệt? | buyer-gui-hang#2 (0.1123); buyer-gui-yeu-cau#0 (0.0783); buyer-nhan-tien#1 (0.0595) | Không có | 0 |

| # | Top-1: nội dung đầu | Agent: đoạn trả về đầu | Nhận xét |
|---|---|---|---|
| Q1 | Một trường hợp được miễn phí chiều hoàn cho shop là khi khách dùng phương thức Tự sắp xếp để gửi lại | Một trường hợp được miễn phí chiều hoàn cho shop là khi khách dùng phương thức Tự sắp xếp để gửi lại sản phẩm. Đây là trách nhiệm của người bán; không | Có markers; cần kiểm tra đủ nghĩa và nguồn |
| Q2 | Thanh toán từ ví ShopeePay: hoàn vào ví trong 24 giờ khi ví hoạt động bình thường. Napas cần 2-5 ngà | Thông thường khâu xử lý mất 3-5 ngày làm việc. Kết quả được cập nhật trong thông báo đơn hàng hoặc email. Nếu được duyệt hoàn tiền, thời gian tiền về  | Không có đủ chứng cứ gold |
| Q3 | ## Bảng 1: Phương thức hoàn tiền và thời gian hoàn tiền  Thời gian dưới đây tính sau khi Shopee chấp | Thời gian dưới đây tính sau khi Shopee chấp nhận hoàn tiền, không tính từ lúc người mua gửi yêu cầu. [1] Có ba lựa chọn: hẹn lấy tại nhà, gửi tại bưu  | Không có đủ chứng cứ gold |
| Q4 | ## 1.1. Nguyên tắc chung  Shopee chưa cung cấp chức năng đổi sản phẩm. Khi món hàng có vấn đề, người | Có ba lựa chọn: hẹn lấy tại nhà, gửi tại bưu cục do hệ thống đề xuất, hoặc Tự sắp xếp. Hai lựa chọn đầu miễn phí cho người mua. Hàng cần đóng gói; ghi | Có markers; cần kiểm tra đủ nghĩa và nguồn |
| Q5 | Cần yêu cầu được duyệt, thông tin vận chuyển chính xác, hành trình tra được và xác nhận giao thành c | Thanh toán từ ví ShopeePay: hoàn vào ví trong 24 giờ khi ví hoạt động bình thường. Napas cần 2-5 ngày làm việc; thanh toán qua ứng dụng ngân hàng cần  | Không có đủ chứng cứ gold |

Có **2/5** câu có chunk đủ bằng chứng trong top-3. Điểm chỉ theo file là
**4/10**, theo nội dung là **3/10**.
Điểm tự động sau kiểm tra marker trong câu trả lời là **3/10**;
đây là điểm hỗ trợ đối chiếu, không phải điểm giảng viên hay chứng minh LLM trả lời
đúng. Xem toàn bộ câu trả lời và nguồn trong [ket_qua_benchmark.txt](../ket_qua_benchmark.txt).

Q5 là failure case rõ: lấy được buyer-nhan-tien nhưng lấy section về ví và lưu ý,
không lấy đoạn thẻ. Doc-only báo hit nhưng câu trả lời không có mốc cần hỏi. Đề xuất:
embedding đa ngữ thật, truy vấn lại theo thẻ và reranker; sau đó đo lại trên cùng
gold, không chỉnh gold theo kết quả truy xuất.

Qua so sánh cấu hình của Trang, heading giúp mỗi mảnh con còn tên mục. Đây là quan
sát từ thí nghiệm tại máy này, không phải trải nghiệm đã nghe Trang thuyết trình.
**Chưa diễn ra demo/trao đổi với nhóm khác; chưa có bài học thực tế để ghi thay.**

## Tự đánh giá

| Tiêu chí | Tự đánh giá tạm thời | Căn cứ |
|---|---|---|
| Warm-up | 5/5 | Công thức và xác nhận bằng code |
| Hướng tiếp cận | 9/10 | Đủ giải thích và giới hạn |
| Code | 30/30 | 42 test gốc pass |
| Similarity | 5/5 | 5 cặp và số đo thật, công khai mock |
| Retrieval | 3/10 | Proxy tự động; chờ chấm đáp án |
| Tổng | 52/60 | Không phải điểm chính thức |

Giới hạn corpus tóm lược và quyền dùng nguồn được ghi trong
[DATA_PROVENANCE.md](DATA_PROVENANCE.md); không tự đánh dấu hoàn tất CP2 nguyên văn.
