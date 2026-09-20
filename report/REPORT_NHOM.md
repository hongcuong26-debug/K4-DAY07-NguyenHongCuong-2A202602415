# Báo cáo nhóm — Lab 07

**Nhóm:** Đạt – Cường – Trang — K4-L3B
**Ngày thực hiện:** 20/09/2026 — **Chủ đề:** Chính sách Trả hàng và Hoàn tiền Shopee.

| Vai trò | Thành viên | MSSV | Chiến lược được phân công |
|---|---|---|---|
| R1 – Data | Nguyễn Tất Đạt | 2A202602578 | FixedSizeChunker(500, overlap=50) |
| R2 – Benchmark | Nguyễn Hồng Cường | 2A202602415 | RecursiveChunker(500) |
| R3 – Strategy | Nguyễn Thị Bảo Trang | 2A202602580 | HeadingChunker(500) |

**Phạm vi bằng chứng:** ba cấu hình được chạy thật trên repo của Cường. Đây là bản
tổng hợp thực nghiệm để nhóm đối chiếu, chưa chứng minh hai thành viên còn lại tự
code/chạy trên repo cá nhân. Không dùng kết quả này thay cho bài cá nhân của họ.

## 1. Lựa chọn tài liệu

Chủ đề có nhiều thời hạn, điều kiện và quy trình; cùng từ vựng nhưng quyền và nghĩa
vụ khác nhau giữa buyer/seller. Phù hợp để kiểm tra chunk có đủ đáp án và metadata
có phân biệt đối tượng được không. Bộ dữ liệu gồm 5 bản ghi ngắn đối chiếu 5 URL
chính thức, không dùng nguồn mẫu hư cấu trong data/ecommerce.

| # | doc_id | Tài liệu / nguồn | Lấy dữ liệu / hiệu lực | Ký tự thân | Metadata |
|---|---|---|---|---|---|
| 1 | buyer-dieu-kien | [Điều kiện và thời hạn yêu cầu của người mua](https://help.shopee.vn/portal/4/article/188931) | 2026-09-20 / not-stated | 773 | buyer; eligibility |
| 2 | buyer-gui-hang | [Cách gửi lại sản phẩm và phí vận chuyển](https://help.shopee.vn/portal/4/article/189477) | 2026-09-20 / not-stated | 808 | buyer; return-shipping |
| 3 | buyer-gui-yeu-cau | [Thao tác tạo yêu cầu trên ứng dụng](https://help.shopee.vn/portal/4/article/79233) | 2026-09-20 / not-stated | 766 | buyer; procedure |
| 4 | buyer-nhan-tien | [Tiền hoàn về đâu và bao lâu](https://help.shopee.vn/portal/4/article/189473) | 2026-09-20 / not-stated | 835 | buyer; refund-payment |
| 5 | seller-phan-hoi | [Phản hồi và trách nhiệm của người bán](https://help.shopee.vn/portal/4/article/77251) | 2026-09-20 / 2026-03-11 | 820 | seller; dispute |

- [x] Đã kiểm tra robots: help.shopee.vn trả HTTP 200, Allow: /.
- [x] Không đăng nhập, không có dữ liệu cá nhân khách hàng, không lưu khóa bí mật.
- [x] Năm file đủ trường bắt buộc, sources.csv khớp 1:1; 4 buyer và 1 seller.
- [x] Giữ số mục nguồn, ngày truy cập và hiệu lực khi nguồn nêu rõ.
- [ ] Chưa có corpus 5 bản chính sách gốc được cấp quyền tái sử dụng; hiện dùng
  các bản ghi diễn đạt lại dữ kiện có nguồn. Không gọi đây là bản crawl nguyên văn.

[DATA_PROVENANCE.md](DATA_PROVENANCE.md) ghi toàn bộ phương pháp, timeout của crawler,
điều khoản nguồn và giới hạn. Cần giảng viên chấp nhận dạng corpus tóm lược hoặc
thay bằng trích đoạn được phép trước khi coi CP2 hoàn tất đầy đủ.

### Metadata schema

| Trường | Kiểu | Ví dụ | Mục đích |
|---|---|---|---|
| doc_id | str | seller-phan-hoi | Định danh file gốc, delete và đánh giá |
| title | str | Phản hồi và trách nhiệm của người bán | Đọc hiểu nguồn |
| source_url | str URL | https://help.shopee.vn/portal/4/article/77251 | Truy vết nguồn chính thức |
| retrieved_at | str ISO date | 2026-09-20 | Thời điểm kiểm tra |
| document_version | str | 2026-03-11 hoặc not-stated | Phân biệt hiệu lực với ngày crawl |
| audience | str enum | buyer / seller | Lọc trước retrieval |
| category | str | dispute | Lọc chủ đề hẹp |
| language | str | vi | Lọc ngôn ngữ |
| collection_method | str | web-read-and-factual-summary | Không nhầm bản ghi với nguyên văn |
| source_sections | str | 5; 7.2; 12.2 | Đối chiếu đúng mục nguồn |

## 2. Thiết kế chiến lược

### Baseline Analysis

`ChunkingStrategyComparator().compare(body, chunk_size=500)` trên 3 tài liệu,
**đã bỏ YAML frontmatter**. Sentence dùng 3 câu/chunk; fixed dùng overlap 50.

| Tài liệu | Chiến lược | Count | Avg length | Ngữ cảnh |
|---|---|---|---|---|
| buyer-dieu-kien | fixed_size | 2 | 411.50 | Có overlap; có thể cắt giữa chữ |
| buyer-dieu-kien | by_sentences | 4 | 191.75 | Giữ dấu câu; không hiểu viết tắt |
| buyer-dieu-kien | recursive | 2 | 386.50 | Ưu tiên đoạn; không overlap |
| buyer-gui-hang | fixed_size | 2 | 429.00 | Có overlap; có thể cắt giữa chữ |
| buyer-gui-hang | by_sentences | 4 | 200.75 | Giữ dấu câu; không hiểu viết tắt |
| buyer-gui-hang | recursive | 3 | 269.33 | Ưu tiên đoạn; không overlap |
| seller-phan-hoi | fixed_size | 2 | 435.00 | Có overlap; có thể cắt giữa chữ |
| seller-phan-hoi | by_sentences | 4 | 203.50 | Giữ dấu câu; không hiểu viết tắt |
| seller-phan-hoi | recursive | 2 | 410.00 | Ưu tiên đoạn; không overlap |

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
metadata filter; chỉ thay chunker. Timestamp UTC: 2026-09-20T03:16:03.996452+00:00.

| Phân công | Chiến lược | Chunk | Avg length | Doc-only /10 | Nội dung /10 | Proxy agent /10 |
|---|---|---|---|---|---|---|
| Đạt | fixed_size | 10 | 425.20 | 5 | 2 | 2 |
| Cường | recursive | 11 | 363.82 | 4 | 3 | 3 |
| Trang | heading | 15 | 272.60 | 4 | 1 | 1 |

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
| Q1 | Tự sắp xếp gửi trả hàng thì tôi có phải trả phí vận chuyển không? | Với vai trò người bán, được miễn phí chiều hoàn khi khách dùng Tự sắp xếp; người mua vẫn phải ứng phí trước. | seller-phan-hoi / 7.2, điểm 5 | {'audience': 'seller'} |
| Q2 | Thực phẩm tươi sống hoặc đông lạnh có thời hạn yêu cầu trả hàng bao lâu và ngoại lệ nào? | 24 giờ từ khi cập nhật giao thành công, ngoại trừ khiếu nại chưa nhận hàng. | buyer-dieu-kien / 1.2 | Không |
| Q3 | Biểu mẫu tạo yêu cầu trả hàng cần điền thông tin và bằng chứng gì trước khi gửi? | Mô tả tình trạng, ảnh hoặc video làm bằng chứng, email liên hệ; kiểm tra rồi gửi. | buyer-gui-yeu-cau / 1, Cách 1, bước 7-8 | Không |
| Q4 | Liệt kê ba hình thức gửi hàng hoàn trả và hình thức nào miễn phí cho người mua? | Hẹn lấy tại nhà, gửi ở bưu cục do hệ thống đề xuất, Tự sắp xếp; hai hình thức đầu miễn phí. | buyer-gui-hang / 1.1 | Không |
| Q5 | Thanh toán bằng thẻ tín dụng hoặc ghi nợ thì tiền hoàn về đâu, sau bao lâu kể từ khi được duyệt? | Về tài khoản thẻ đã thanh toán trong 7-14 ngày làm việc tùy ngân hàng, tính sau khi Shopee chấp nhận hoàn tiền. | buyer-nhan-tien / Bảng 1 | Không |

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
| Q1 | 1 / 2 | 1 / 2 | 2 / 1 |
| Q2 | - / 0 | - / 0 | - / 0 |
| Q3 | - / 0 | - / 0 | - / 0 |
| Q4 | - / 0 | 3 / 1 | - / 0 |
| Q5 | - / 0 | - / 0 | - / 0 |

### A/B Q1 trên cả ba chiến lược

| Chiến lược | Filter | Top-3 với score | Audience theo thứ tự | Hạng chứng cứ |
|---|---|---|---|---|
| fixed_size | seller | seller-phan-hoi#1 (0.0707); seller-phan-hoi#0 (0.0106) | seller, seller | 1 |
| fixed_size | Không lọc | buyer-nhan-tien#0 (0.2434); buyer-gui-hang#1 (0.1083); seller-phan-hoi#1 (0.0707) | buyer, buyer, seller | 3 |
| recursive | seller | seller-phan-hoi#1 (0.1759); seller-phan-hoi#0 (-0.0091) | seller, seller | 1 |
| recursive | Không lọc | seller-phan-hoi#1 (0.1759); buyer-nhan-tien#0 (0.0537); buyer-gui-hang#0 (0.0265) | seller, buyer, buyer | 1 |
| heading | seller | seller-phan-hoi#0 (0.0405); seller-phan-hoi#1 (0.0195); seller-phan-hoi#2 (-0.1129) | seller, seller, seller | 2 |
| heading | Không lọc | buyer-dieu-kien#2 (0.2257); buyer-dieu-kien#0 (0.1388); buyer-nhan-tien#1 (0.1355) | buyer, buyer, buyer | Không có |

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

### Kịch bản demo 7 phút (chuẩn bị, chưa trình bày)

- 0:00–1:00 Đạt giới thiệu chủ đề, nguồn, buyer/seller và giới hạn corpus.
- 1:00–2:00 Đạt trình bày fixed/overlap; Cường trình bày recursive.
- 2:00–3:00 Trang giải thích heading lặp lại trên mảnh dài.
- 3:00–4:30 Cường mở kết quả Q1 có/không filter và Q3 heading sai section.
- 4:30–6:00 Chạy `python bench.py`, mở JSON/TXT để chỉ đúng chunk nguồn.
- 6:00–7:00 Cả nhóm giải thích mock, đánh đổi precision/recall, kế hoạch đo model thật.

Nếu đổi chủ đề, fixed/recursive vẫn dùng được, heading chỉ phù hợp văn bản có cấu
trúc tiêu đề. Bài học tại máy này là đúng file chưa đủ và filter không cứu được
sai section cùng đối tượng. **Chưa có demo hoặc phản hồi nhóm khác; không ghi nhận
một trải nghiệm chưa diễn ra.** Nếu làm lại: xin nguồn được phép tái sử dụng, bổ sung
seller, giữ benchmark cố định và chạy model đa ngữ với cache nội dung.

## Tự đánh giá và trạng thái nộp

| Hạng mục | Tự đánh giá tạm | Giới hạn |
|---|---|---|
| Dữ liệu | Chưa chốt /10 | 5 file đủ metadata nhưng là bản tóm lược; xem provenance |
| Chiến lược | 12/15 | Có baseline và ba cấu hình; cần thành viên chạy độc lập |
| Retrieval | 3/10 | Proxy với mock; cần chấm nội dung agent |
| Demo | Chưa chấm /5 | Đã có kịch bản, chưa trình bày |
| Tổng | Chưa chốt /40 | Không tự nhận điểm cho phần chưa hoàn thành |

- [x] Code 42/42; benchmark cá nhân và ba cấu hình có log thật.
- [x] Metadata/manifest và gold được script kiểm tra.
- [ ] Giảng viên chấp nhận corpus tóm lược hoặc thay bằng corpus được phép dùng.
- [ ] Đạt/Trang xác nhận kết quả bài riêng; hoàn thành demo.
- [ ] Push GitHub thành công và nộp link/rating trên vlearn.

Repo dự kiến nộp: https://github.com/hongcuong26-debug/K4-DAY07-NguyenHongCuong-2A202602415
