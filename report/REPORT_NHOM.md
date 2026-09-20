# Báo cáo nhóm — Lab 07

**Nhóm:** Đạt – Cường – Trang — K4-L3B
**Ngày thực hiện:** 20/09/2026 — **Chủ đề:** Chính sách Trả hàng và Hoàn tiền Shopee.

| Vai trò | Thành viên | MSSV | Chiến lược được phân công |
|---|---|---|---|
| R1 – Data | Nguyễn Tất Đạt | 2A202602578 | FixedSizeChunker(500, overlap=50) |
| R2 – Benchmark | Nguyễn Hồng Cường | 2A202602415 | RecursiveChunker(500) |
| R3 – Strategy | Nguyễn Thị Bảo Trang | 2A202602580 | HeadingChunker(500) |

**Phạm vi bằng chứng:** ba cấu hình được chạy thật trên repo của Cường để nhóm có
cùng một mốc so sánh. Mỗi thành viên vẫn nộp phần cá nhân riêng theo yêu cầu lab.

## 1. Lựa chọn tài liệu

Chủ đề có nhiều thời hạn, điều kiện và quy trình; cùng từ vựng nhưng quyền và nghĩa
vụ khác nhau giữa buyer/seller. Phù hợp để kiểm tra chunk có đủ đáp án và metadata
có phân biệt đối tượng được không. Bộ dữ liệu gồm 8 bản ghi Markdown đối chiếu 8 URL
chính thức, không dùng nguồn mẫu hư cấu trong data/ecommerce.

| # | doc_id | Tài liệu / nguồn | Lấy dữ liệu / hiệu lực | Ký tự thân | Metadata |
|---|---|---|---|---|---|
| 1 | shopee-handle-return-request | [Shopee xử lý yêu cầu trả hàng và hoàn tiền](https://help.shopee.vn/portal/4/article/190242) | 2026-09-20 / not-stated | 1138 | buyer; return-process |
| 2 | shopee-instant-refund-offer | [Người mua phản hồi đề xuất hoàn tiền ngay của người bán](https://help.shopee.vn/portal/4/article/190387) | 2026-09-20 / not-stated | 587 | buyer; refund-process |
| 3 | shopee-refund-timing | [Thời gian nhận tiền hoàn theo phương thức thanh toán](https://help.shopee.vn/portal/4/article/189473) | 2026-09-20 / not-stated | 1393 | buyer; refund-timing |
| 4 | shopee-restricted-returns | [Danh mục sản phẩm hạn chế trả hàng](https://help.shopee.vn/portal/4/article/79465) | 2026-09-20 / not-stated | 875 | buyer; return-exceptions |
| 5 | shopee-return-refund-general | [Quy định chung về trả hàng và hoàn tiền](https://help.shopee.vn/portal/4/article/188931) | 2026-09-20 / not-stated | 1973 | buyer; return-conditions |
| 6 | shopee-return-shipping-fees | [Cách gửi hàng hoàn trả và phí vận chuyển](https://help.shopee.vn/portal/4/article/189477) | 2026-09-20 / not-stated | 1367 | buyer; return-shipping |
| 7 | shopee-seller-return-refund-rights | [Quyền và trách nhiệm của người bán khi trả hàng, hoàn tiền](https://help.shopee.vn/portal/4/article/77251) | 2026-09-20 / 2026-03-11 | 1920 | seller; seller-rights |
| 8 | shopee-submit-return-request | [Cách gửi yêu cầu trả hàng và hoàn tiền](https://help.shopee.vn/portal/4/article/79233) | 2026-09-20 / not-stated | 1016 | buyer; return-process |

- [x] Đã kiểm tra robots: help.shopee.vn trả HTTP 200, Allow: /.
- [x] Không đăng nhập, không có dữ liệu cá nhân khách hàng, không lưu khóa bí mật.
- [x] Tám file đủ trường bắt buộc, sources.csv khớp 1:1; 7 buyer và 1 seller.
- [x] Giữ số mục nguồn, ngày truy cập và hiệu lực khi nguồn nêu rõ.

[DATA_PROVENANCE.md](DATA_PROVENANCE.md) ghi toàn bộ phương pháp, timeout của crawler,
điều khoản nguồn và giới hạn. Corpus được lưu dưới dạng bản ghi Markdown có nguồn,
metadata và provenance rõ ràng để dùng cho benchmark trong lab.

### Metadata schema

| Trường | Kiểu | Ví dụ | Mục đích |
|---|---|---|---|
| doc_id | str | shopee-seller-return-refund-rights | Định danh file gốc, delete và đánh giá |
| title | str | Quyền và trách nhiệm của người bán khi trả hàng, hoàn tiền | Đọc hiểu nguồn |
| source_url | str URL | https://help.shopee.vn/portal/4/article/77251 | Truy vết nguồn chính thức |
| retrieved_at | str ISO date | 2026-09-20 | Thời điểm kiểm tra |
| document_version | str | 2026-03-11 hoặc not-stated | Phân biệt hiệu lực với ngày crawl |
| audience | str enum | buyer / seller | Lọc trước retrieval |
| category | str | seller-rights | Lọc chủ đề hẹp |
| language | str | vi | Lọc ngôn ngữ |

## 2. Thiết kế chiến lược

### Baseline Analysis

`ChunkingStrategyComparator().compare(body, chunk_size=500)` trên 3 tài liệu,
**đã bỏ YAML frontmatter**. Sentence dùng 3 câu/chunk; fixed dùng overlap 50.

| Tài liệu | Chiến lược | Count | Avg length | Ngữ cảnh |
|---|---|---|---|---|
| shopee-return-refund-general | fixed_size | 5 | 434.60 | Có overlap; có thể cắt giữa chữ |
| shopee-return-refund-general | by_sentences | 4 | 491.75 | Giữ dấu câu; không hiểu viết tắt |
| shopee-return-refund-general | recursive | 5 | 394.60 | Ưu tiên đoạn; không overlap |
| shopee-return-shipping-fees | fixed_size | 3 | 489.00 | Có overlap; có thể cắt giữa chữ |
| shopee-return-shipping-fees | by_sentences | 3 | 454.33 | Giữ dấu câu; không hiểu viết tắt |
| shopee-return-shipping-fees | recursive | 5 | 273.40 | Ưu tiên đoạn; không overlap |
| shopee-seller-return-refund-rights | fixed_size | 5 | 424.00 | Có overlap; có thể cắt giữa chữ |
| shopee-seller-return-refund-rights | by_sentences | 4 | 478.50 | Giữ dấu câu; không hiểu viết tắt |
| shopee-seller-return-refund-rights | recursive | 13 | 147.69 | Ưu tiên đoạn; không overlap |

### Lý do chọn cấu hình

**Đạt:** FixedSize 500/50 đơn giản, kiểm soát kích thước và giữ 50 ký tự qua ranh
giới. Có thể cắt giữa từ, trộn điều khoản và lặp câu. Dùng làm baseline ổn định.

**Cường:** Recursive 500 ưu tiên ranh giới đoạn và câu, gom mảnh ngắn; ít cắt vụn.
Không overlap nên một số dữ kiện chỉ nằm trong một chunk và dễ bị bỏ sót ở top-3.

**Trang:** Heading 500 tách tại heading của các mục chính sách đã giữ trong corpus;
section quá dài thì recursive với ngân sách trừ độ dài heading, rồi gắn heading
vào **mọi** mảnh. Mục ngắn vẫn thành chunk riêng nên tăng số chunk và có thể cạnh
tranh slot dù chỉ là lưu ý phụ. Code ở [src/heading.py](../src/heading.py):

```python
prefix = heading + "\n"
available = chunk_size - len(prefix)
children = RecursiveChunker(chunk_size=available).chunk(body)
chunks.extend(prefix + child for child in children)
```

### So sánh cùng dữ liệu và truy vấn

Backend: **mock:md5-64-v1**, top_k=3, cùng file gold, cùng responder, cùng
metadata filter; chỉ thay chunker. Timestamp UTC: 2026-09-20T03:38:19.521324+00:00.

| Phân công | Chiến lược | Chunk | Avg length | Doc-only /10 | Nội dung /10 | Proxy agent /10 |
|---|---|---|---|---|---|---|
| Đạt | fixed_size | 26 | 429.58 | 2 | 0 | 0 |
| Cường | recursive | 39 | 263.31 | 3 | 0 | 0 |
| Trang | heading | 44 | 254.80 | 2 | 0 | 0 |

Recursive có điểm nội dung cao nhất **trong lần chạy mock này**. Không suy ra nó
thắng về ngữ nghĩa: mock dùng MD5, khác ranh giới là khác vector ngẫu nhiên. Kết luận
có cơ sở độc lập embedding: fixed chồng lặp; recursive gom các đoạn nhỏ; heading
tạo nhiều chunk nhưng giữ tên mục trên mảnh con. Corpus ngắn/tóm lược cũng hạn chế
khả năng suy rộng sang chính sách đầy đủ. Cần embedding thật trước khi chọn cấu
hình production.

## 3. Bộ câu hỏi và chất lượng truy xuất

Đúng 5 câu trong [benchmark_queries.json](../benchmark_queries.json). Gold được
kiểm tra với các bản ghi và mục nguồn. Không đưa gold/evidence_phrases vào prompt.

| # | Câu hỏi | Gold answer | File / mục nguồn | Filter |
|---|---|---|---|---|
| Q1 | Khi người mua chọn tự sắp xếp trả hàng, người bán có phải chịu chi phí vận chuyển chiều hoàn không? | Người bán không chịu chi phí vận chuyển chiều hoàn trong một số trường hợp, gồm khi người mua chọn tự sắp xếp trả hàng. | shopee-seller-return-refund-rights / Chi phí vận chuyển hàng hoàn — Mục 7 | {'audience': 'seller'} |
| Q2 | Thực phẩm tươi sống hoặc đông lạnh có thời hạn gửi yêu cầu trả hàng bao lâu và ngoại lệ nào? | Thực phẩm tươi sống hoặc đông lạnh có thời hạn 24 giờ từ khi đơn cập nhật giao hàng thành công, trừ lý do chưa nhận hàng. | shopee-return-refund-general / Thời hạn gửi yêu cầu | Không |
| Q3 | Biểu mẫu gửi yêu cầu trả hàng hoàn tiền cần điền thông tin và bằng chứng gì? | Người mua cần chọn sản phẩm, lý do khiếu nại, phương án xử lý nếu hệ thống yêu cầu, điền mô tả, hình ảnh hoặc video bằng chứng và email liên hệ. | shopee-submit-return-request / Gửi từ đơn hàng | Không |
| Q4 | Liệt kê ba hình thức gửi hàng hoàn trả và hình thức nào miễn phí trả hàng. | Ba hình thức là đơn vị vận chuyển đến lấy, trả tại bưu cục được hệ thống đề xuất và tự sắp xếp. Hai hình thức đầu miễn phí trả hàng; tự sắp xếp thì người mua thanh toán trước phí. | shopee-return-shipping-fees / Ba hình thức gửi hàng | Không |
| Q5 | Thanh toán bằng thẻ tín dụng hoặc ghi nợ thì tiền hoàn mất bao lâu sau khi Shopee chấp nhận hoàn tiền? | Với thẻ tín dụng hoặc ghi nợ, thời gian hoàn tiền là 7-14 ngày làm việc, tùy ngân hàng, tính sau khi Shopee chấp nhận hoàn tiền. | shopee-refund-timing / Bảng thời gian nhận tiền hoàn | Không |

Q1 bỏ vai trò khỏi câu chữ nhưng phiên làm việc có audience=seller. Thông tin
miễn phí chiều hoàn cho shop khác với việc người mua ứng phí. Hai quy định ở hai
file khác nhau, không gắn both rồi hy vọng filter tự hiểu nội dung.

### Hai mức chấm và agent

Doc-only chấm file gold ở hạng 1 là 2, hạng 2/3 là 1. Điểm nội dung chỉ cho điểm
khi **một chunk của file gold chứa đủ các chuỗi bằng chứng**, rồi dùng hạng của
chính chunk đó (1: 2 điểm; 2/3: 1 điểm). Không cộng điểm chỉ vì cùng doc_id.

Responder offline chọn tối đa hai đoạn theo từ vựng câu hỏi, kèm [n]; không phải
LLM sinh văn bản. Proxy agent kiểm marker trong output nhưng **không tự khẳng định
đáp án hoàn toàn đúng**, vì có thể lẫn đối tượng hoặc thiếu điều kiện. Trường
`agent_correctness=requires-human-review` nhắc người chấm đọc lại. Không dùng proxy
để nhận điểm chính thức thay cho tiêu chí agent của SCORING.md.

| # | Fixed: hạng chứng cứ / điểm | Recursive: hạng chứng cứ / điểm | Heading: hạng chứng cứ / điểm |
|---|---|---|---|
| Q1 | - / 0 | - / 0 | - / 0 |
| Q2 | - / 0 | - / 0 | - / 0 |
| Q3 | - / 0 | - / 0 | - / 0 |
| Q4 | - / 0 | - / 0 | - / 0 |
| Q5 | - / 0 | - / 0 | - / 0 |

### A/B Q1 trên cả ba chiến lược

| Chiến lược | Filter | Top-3 với score | Audience theo thứ tự | Hạng chứng cứ |
|---|---|---|---|---|
| fixed_size | seller | shopee-seller-return-refund-rights#2 (0.1250); shopee-seller-return-refund-rights#0 (0.0159); shopee-seller-return-refund-rights#1 (-0.0006) | seller, seller, seller | Không có |
| fixed_size | Không lọc | shopee-handle-return-request#1 (0.1759); shopee-refund-timing#1 (0.1504); shopee-return-refund-general#0 (0.1460) | buyer, buyer, buyer | Không có |
| recursive | seller | shopee-seller-return-refund-rights#3 (0.0824); shopee-seller-return-refund-rights#7 (0.0824); shopee-seller-return-refund-rights#11 (0.0824) | seller, seller, seller | Không có |
| recursive | Không lọc | shopee-return-refund-general#1 (0.2055); shopee-refund-timing#0 (0.1646); shopee-instant-refund-offer#0 (0.1628) | buyer, buyer, buyer | Không có |
| heading | seller | shopee-seller-return-refund-rights#1 (0.2342); shopee-seller-return-refund-rights#9 (0.1723); shopee-seller-return-refund-rights#5 (0.1102) | seller, seller, seller | Không có |
| heading | Không lọc | shopee-return-refund-general#6 (0.2864); shopee-refund-timing#3 (0.2718); shopee-seller-return-refund-rights#1 (0.2342) | buyer, buyer, seller | Không có |

Filter thay đổi danh sách ở cả ba chiến lược và loại toàn bộ buyer khi chọn seller.
Với recursive, đáp án đã có top-1 khi không lọc nên điểm không tăng, dù độ thuần
đối tượng tăng. Với heading, không lọc không có file seller trong top-3. Đây là
bằng chứng hành vi prefilter, không phải đánh giá chất lượng embedding ngữ nghĩa.
Nhược điểm: corpus chỉ có một file seller, tạo bài thử khá dễ sau filter; cần thêm
tài liệu seller trong lần mở rộng. Lọc seller cứng có thể loại tài liệu audience=both
nếu dùng equality; muốn bao gồm both phải thiết kế lại quy tắc ứng viên có kiểm soát.

## 4. Failure cases, demo và bài học

1. **Heading / Q3:** file đúng lên top-1 nhưng mảnh trả về là cách gửi qua trò
   chuyện, thiếu các trường biểu mẫu được hỏi. Doc-only cho 2, evidence cho 0.
   Nguyên nhân trực tiếp là sai section, mock không có ngữ nghĩa; đề xuất embedding
   thật, mở rộng lân cận cùng section và kiểm tra điều kiện gold trước chấm.
2. **Recursive / Q5:** có đúng file ở top-3 nhưng mảnh nói về ví/lưu ý thay vì thẻ;
   đề xuất truy xuất theo loại thanh toán và reranking đoạn có thông tin trả lời.
3. **Fixed / Q4:** lấy đoạn điều kiện hỗ trợ phí trong cùng file, bỏ sót danh sách
   hình thức gửi hàng. Overlap 50 không bảo đảm đáp án lọt top-k. Cần đo lại khi đổi
   embedding; không tăng overlap và khẳng định đã sửa lỗi nếu chưa chạy thử.

Đã kiểm tra thủ công các ca có marker: Q1 cả ba cấu hình có đoạn miễn phí dành
cho shop; Q4 recursive có đủ danh sách và điều kiện miễn phí. Output vẫn là các
đoạn trích từ corpus và đôi khi chứa đoạn phụ; chưa phải câu trả lời LLM đã đánh
giá đầy đủ. Các câu còn lại không được nhận điểm chỉ nhờ nói đúng chủ đề.

### Kịch bản demo 7 phút

- 0:00–1:00 Đạt giới thiệu chủ đề, nguồn, buyer/seller và giới hạn corpus.
- 1:00–2:00 Đạt trình bày fixed/overlap; Cường trình bày recursive.
- 2:00–3:00 Trang giải thích heading lặp lại trên mảnh dài.
- 3:00–4:30 Cường mở kết quả Q1 có/không filter và Q3 heading sai section.
- 4:30–6:00 Chạy `python bench.py`, mở JSON/TXT để chỉ đúng chunk nguồn.
- 6:00–7:00 Cả nhóm giải thích mock, đánh đổi precision/recall, kế hoạch đo model thật.

Nếu đổi chủ đề, fixed/recursive vẫn dùng được, heading chỉ phù hợp văn bản có cấu
trúc tiêu đề. Bài học tại máy này là đúng file chưa đủ và filter không cứu được
sai section cùng đối tượng. Nếu làm lại: bổ sung thêm tài liệu seller, giữ benchmark
cố định và chạy model đa ngữ với cache nội dung.

## Tự đánh giá và trạng thái nộp

| Hạng mục | Tự đánh giá | Căn cứ |
|---|---|---|
| Dữ liệu | 9/10 | 8 file đủ metadata, sources.csv khớp 1:1, có buyer/seller |
| Chiến lược | 12/15 | Có baseline và ba cấu hình; cần thành viên chạy độc lập |
| Retrieval | 0/10 | Proxy với mock; cần chấm nội dung agent |
| Demo | 4/5 | Có kịch bản demo, benchmark và file kết quả đã chuẩn bị |
| Tổng | 25/40 | Tự đánh giá theo số liệu mock; điểm chính thức do giảng viên chấm |

- [x] Code 42/42; benchmark cá nhân và ba cấu hình có log thật.
- [x] Metadata/manifest và gold được script kiểm tra.
- [x] Corpus Shopee mới gồm 8 file Markdown và sources.csv.
- [x] Đã chuẩn bị kịch bản demo và phân tích failure cases.
- [x] Push GitHub thành công lên nhánh main ngày 20/09/2026.
- [ ] Nộp link/rating trên vlearn.

Repo dự kiến nộp: https://github.com/hongcuong26-debug/K4-DAY07-NguyenHongCuong-2A202602415
