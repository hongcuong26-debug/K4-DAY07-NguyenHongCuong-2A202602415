"""Build the two reports from actual saved benchmark/test evidence."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench import read_document
from src.chunking import ChunkingStrategyComparator, FixedSizeChunker, compute_similarity
from src.embeddings import MockEmbedder

REPORT = ROOT / "report"
benchmark = json.loads((REPORT / "benchmark_all.json").read_text(encoding="utf-8"))
personal = json.loads((ROOT / "ket_qua_benchmark.json").read_text(encoding="utf-8"))
assert benchmark["query_sha256"] == personal["query_sha256"]
runs = {r["strategy"]: r for r in benchmark["runs"]}
mine = personal["runs"][0]
assert mine["strategy"] == "recursive"
assert mine["corpus_sha256"] == runs["recursive"]["corpus_sha256"]
assert mine["queries"] == runs["recursive"]["queries"]
corpus = {p.stem: read_document(p) for p in sorted((ROOT / "data/shopee-doi-tra-hoan-tien").glob("*.md"))}
pairs = [
    ("Tôi muốn gửi lại món hàng vì bị hỏng.", "Sản phẩm lỗi nên tôi đề nghị lấy lại tiền.", "cao"),
    ("Tiền được chuyển lại về thẻ đã thanh toán.", "Khoản hoàn trả đi vào tài khoản thẻ dùng lúc mua.", "cao"),
    ("Hạn gửi yêu cầu là mười lăm ngày.", "Tối nay tôi đi xem phim.", "thấp"),
    ("Người bán phải phản hồi khiếu nại đúng hạn.", "Một tam giác có ba cạnh.", "thấp"),
    ("Bạn cần quay video khi mở kiện hàng.", "Hãy ghi hình lúc bóc gói để có bằng chứng.", "cao"),
]
embedder = MockEmbedder()
pair_results = [{"a": a, "b": b, "prediction": prediction,
                 "actual": compute_similarity(embedder(a), embedder(b))} for a, b, prediction in pairs]
baseline = {name: ChunkingStrategyComparator().compare(corpus[name][1], chunk_size=500)
            for name in ["shopee-return-refund-general", "shopee-return-shipping-fees",
                         "shopee-seller-return-refund-rights"]}
stats = {"backend": "MockEmbedder md5-64-v1", "warmup": {str(o): len(FixedSizeChunker(500, o).chunk('a' * 10000)) for o in [50, 100]},
         "baseline": baseline, "pairs": pair_results}
(REPORT / "analysis_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] +
                     ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows])


def top3(q):
    return "; ".join(f"{r['id']} ({r['score']:.4f})" for r in q["top3"])


def prediction_label(pair):
    measured = "cao" if pair["actual"] >= 0.7 else ("thấp" if pair["actual"] <= 0.3 else "trung bình")
    return "Trùng nhãn; không chứng minh ngữ nghĩa" if measured == pair["prediction"] else "Không"


pytest_output = (REPORT / "pytest_output.txt").read_text(encoding="utf-8").strip()
assert "42 passed" in pytest_output
correct = sum(q["evidence_rank"] is not None for q in mine["queries"])
personal_text = f"""# Báo cáo cá nhân — Lab 07

**Họ tên:** Nguyễn Hồng Cường — **MSSV:** 2A202602415
**Lớp:** K4-L3B — **Nhóm:** G18
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
- Chạy FixedSizeChunker xác nhận: {stats['warmup']}. Overlap lớn giúp giữ câu/điều
  kiện nằm sát ranh giới, đổi lại tốn embedding, bộ nhớ và dễ lấy kết quả trùng lặp.

## 2. Hướng tiếp cận

**SentenceChunker:** dùng `(?<=[.!?])\\s+`, tách ở khoảng trắng sau dấu kết câu nên
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
{pytest_output}
```

## 4. Dự đoán độ tương tự

Backend: **MockEmbedder, MD5, 64 chiều**. Dự đoán là về nghĩa câu; số đo thật là
mock nên không dùng để kết luận model hiểu nghĩa. Quy ước minh họa: cao >= 0.7,
thấp <= 0.3, còn lại trung bình; đây không phải ngưỡng được hiệu chuẩn cho hệ thật.

{table(['#', 'Câu A', 'Câu B', 'Dự đoán', 'Cosine thực đo', 'Đúng nhãn?'], [(i, p['a'], p['b'], p['prediction'], f"{p['actual']:.6f}", prediction_label(p)) for i, p in enumerate(pair_results, 1)])}

Bất ngờ là các cặp diễn đạt tương đương vẫn có điểm thấp. Nguyên nhân đã biết:
mock băm chuỗi rồi sinh vector, không học nghĩa. Cặp thấp có điểm thấp cũng chỉ là
sự trùng hợp trong thí nghiệm này. Muốn đánh giá ngữ nghĩa cần chạy lại model đa ngữ.

## 5. Kết quả truy xuất riêng

Chạy `python bench.py` (mặc định recursive), backend **{personal['backend']}**;
thời điểm UTC {personal['run_at']}. Chỉ dùng corpus Shopee, không trộn dữ liệu mẫu.
Nạp **{mine['count']} chunk**, trung bình **{mine['avg_length']:.2f} ký tự**.

{table(['#', 'Câu hỏi', 'Top-3: chunk (cosine)', 'Hạng có đủ đáp án', 'Điểm nội dung /2'], [(q['id'], q['query'], top3(q), q['evidence_rank'] or 'Không có', q['evidence_score']) for q in mine['queries']])}

{table(['#', 'Top-1: nội dung đầu', 'Agent: đoạn trả về đầu', 'Nhận xét'], [(q['id'], q['top3'][0]['content'][:100], q['agent_answer'][:150], 'Có markers; cần kiểm tra đủ nghĩa và nguồn' if q['answer_marker_match'] else 'Không có đủ chứng cứ gold') for q in mine['queries']])}

Có **{correct}/5** câu có chunk đủ bằng chứng trong top-3. Điểm chỉ theo file là
**{mine['doc_only_score']}/10**, theo nội dung là **{mine['evidence_score']}/10**.
Điểm tự động sau kiểm tra marker trong câu trả lời là **{mine['automatic_score']}/10**;
đây là điểm hỗ trợ đối chiếu, không phải điểm giảng viên hay chứng minh LLM trả lời
đúng. Xem toàn bộ câu trả lời và nguồn trong [ket_qua_benchmark.txt](../ket_qua_benchmark.txt).

Q1 là failure case rõ của mock + recursive: filter seller đưa đúng file người bán vào
top-3, nhưng các chunk được xếp hạng không chứa đủ cụm chứng cứ cần thiết. Doc-only
báo hit, còn evidence-score vẫn bằng 0. Đề xuất: dùng embedding đa ngữ thật, tăng
overlap hoặc dùng heading chunker có gắn tiêu đề cho mọi mảnh con; sau đó đo lại trên
cùng gold, không chỉnh gold theo kết quả truy xuất.

Qua so sánh cấu hình của Trang, heading giúp mỗi mảnh con còn tên mục. Đây là điểm
hữu ích khi chính sách được chia theo heading, vì các mảnh con không bị mất ngữ cảnh
về mục đang nói. Bài học chính là đúng file chưa đủ; retrieval phải lấy đúng section
có câu trả lời.

## Tự đánh giá

{table(['Tiêu chí', 'Tự đánh giá tạm thời', 'Căn cứ'], [('Warm-up','5/5','Công thức và xác nhận bằng code'),('Hướng tiếp cận','9/10','Đủ giải thích và giới hạn'),('Code','30/30','42 test gốc pass'),('Similarity','5/5','5 cặp và số đo thật, công khai mock'),('Retrieval',f"{mine['automatic_score']}/10",'Proxy tự động; chờ chấm đáp án'),('Tổng',f"{49 + mine['automatic_score']}/60",'Không phải điểm chính thức')])}

Corpus và nguồn được ghi trong [DATA_PROVENANCE.md](DATA_PROVENANCE.md). Phần cá
nhân đã hoàn tất với code 42/42, benchmark riêng, phân tích lỗi và báo cáo kết quả.
"""
(REPORT / "REPORT_CANHAN.md").write_text("\n".join(line.rstrip() for line in personal_text.splitlines()) + "\n", encoding="utf-8")

inventory = [(i, doc_id, f"[{m['title']}]({m['source_url']})", m['retrieved_at'] + ' / ' + m['document_version'], len(body), m['audience'] + '; ' + m['category'])
             for i, (doc_id, (m, body)) in enumerate(corpus.items(), 1)]
baseline_rows = [(doc_id, name, value['count'], f"{value['avg_length']:.2f}",
                  {'fixed_size':'Có overlap; có thể cắt giữa chữ', 'by_sentences':'Giữ dấu câu; không hiểu viết tắt', 'recursive':'Ưu tiên đoạn; không overlap'}[name])
                 for doc_id, strategies in baseline.items() for name, value in strategies.items()]
members = {'fixed_size':'Đạt', 'recursive':'Cường', 'heading':'Trang'}
ab_rows = []
for name, trial in runs.items():
    q = trial['queries'][0]
    for label, entry in [('seller', q), ('Không lọc', q['without_filter'])]:
        ab_rows.append((name, label, top3(entry), ', '.join(r['metadata']['audience'] for r in entry['top3']), entry['evidence_rank'] or 'Không có'))
group_text = f"""# Báo cáo nhóm — Lab 07

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

{table(['#', 'doc_id', 'Tài liệu / nguồn', 'Lấy dữ liệu / hiệu lực', 'Ký tự thân', 'Metadata'], inventory)}

- [x] Đã kiểm tra robots: help.shopee.vn trả HTTP 200, Allow: /.
- [x] Không đăng nhập, không có dữ liệu cá nhân khách hàng, không lưu khóa bí mật.
- [x] Tám file đủ trường bắt buộc, sources.csv khớp 1:1; 7 buyer và 1 seller.
- [x] Giữ số mục nguồn, ngày truy cập và hiệu lực khi nguồn nêu rõ.

[DATA_PROVENANCE.md](DATA_PROVENANCE.md) ghi toàn bộ phương pháp, timeout của crawler,
điều khoản nguồn và giới hạn. Corpus được lưu dưới dạng bản ghi Markdown có nguồn,
metadata và provenance rõ ràng để dùng cho benchmark trong lab.

### Metadata schema

{table(['Trường', 'Kiểu', 'Ví dụ', 'Mục đích'], [('doc_id','str','shopee-seller-return-refund-rights','Định danh file gốc, delete và đánh giá'),('title','str','Quyền và trách nhiệm của người bán khi trả hàng, hoàn tiền','Đọc hiểu nguồn'),('source_url','str URL','https://help.shopee.vn/portal/4/article/77251','Truy vết nguồn chính thức'),('retrieved_at','str ISO date','2026-09-20','Thời điểm kiểm tra'),('document_version','str','2026-03-11 hoặc not-stated','Phân biệt hiệu lực với ngày crawl'),('audience','str enum','buyer / seller','Lọc trước retrieval'),('category','str','seller-rights','Lọc chủ đề hẹp'),('language','str','vi','Lọc ngôn ngữ')])}

## 2. Thiết kế chiến lược

### Baseline Analysis

`ChunkingStrategyComparator().compare(body, chunk_size=500)` trên 3 tài liệu,
**đã bỏ YAML frontmatter**. Sentence dùng 3 câu/chunk; fixed dùng overlap 50.

{table(['Tài liệu', 'Chiến lược', 'Count', 'Avg length', 'Ngữ cảnh'], baseline_rows)}

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
prefix = heading + "\\n"
available = chunk_size - len(prefix)
children = RecursiveChunker(chunk_size=available).chunk(body)
chunks.extend(prefix + child for child in children)
```

### So sánh cùng dữ liệu và truy vấn

Backend: **{benchmark['backend']}**, top_k=3, cùng file gold, cùng responder, cùng
metadata filter; chỉ thay chunker. Timestamp UTC: {benchmark['run_at']}.

{table(['Phân công', 'Chiến lược', 'Chunk', 'Avg length', 'Doc-only /10', 'Nội dung /10', 'Proxy agent /10'], [(members[n], n, r['count'], f"{r['avg_length']:.2f}", r['doc_only_score'], r['evidence_score'], r['automatic_score']) for n, r in runs.items()])}

Recursive có điểm nội dung cao nhất **trong lần chạy mock này**. Không suy ra nó
thắng về ngữ nghĩa: mock dùng MD5, khác ranh giới là khác vector ngẫu nhiên. Kết luận
có cơ sở độc lập embedding: fixed chồng lặp; recursive gom các đoạn nhỏ; heading
tạo nhiều chunk nhưng giữ tên mục trên mảnh con. Corpus ngắn/tóm lược cũng hạn chế
khả năng suy rộng sang chính sách đầy đủ. Cần embedding thật trước khi chọn cấu
hình production.

## 3. Bộ câu hỏi và chất lượng truy xuất

Đúng 5 câu trong [benchmark_queries.json](../benchmark_queries.json). Gold được
kiểm tra với các bản ghi và mục nguồn. Không đưa gold/evidence_phrases vào prompt.

{table(['#', 'Câu hỏi', 'Gold answer', 'File / mục nguồn', 'Filter'], [(q['id'], q['query'], q['gold_answer'], q['gold_doc_id'] + ' / ' + q['source_section'], q.get('metadata_filter') or 'Không') for q in mine['queries']])}

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

{table(['#', 'Fixed: hạng chứng cứ / điểm', 'Recursive: hạng chứng cứ / điểm', 'Heading: hạng chứng cứ / điểm'], [(f'Q{i+1}', *[f"{runs[n]['queries'][i]['evidence_rank'] or '-'} / {runs[n]['queries'][i]['evidence_score']}" for n in runs]) for i in range(5)])}

### A/B Q1 trên cả ba chiến lược

{table(['Chiến lược', 'Filter', 'Top-3 với score', 'Audience theo thứ tự', 'Hạng chứng cứ'], ab_rows)}

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

{table(['Hạng mục', 'Tự đánh giá', 'Căn cứ'], [('Dữ liệu','9/10','8 file đủ metadata, sources.csv khớp 1:1, có buyer/seller'),('Chiến lược','12/15','Có baseline và ba cấu hình; cần thành viên chạy độc lập'),('Retrieval',f"{max(r['automatic_score'] for r in runs.values())}/10",'Proxy với mock; cần chấm nội dung agent'),('Demo','4/5','Có kịch bản demo, benchmark và file kết quả đã chuẩn bị'),('Tổng',f"{25 + max(r['automatic_score'] for r in runs.values())}/40",'Tự đánh giá theo số liệu mock; điểm chính thức do giảng viên chấm')])}

- [x] Code 42/42; benchmark cá nhân và ba cấu hình có log thật.
- [x] Metadata/manifest và gold được script kiểm tra.
- [x] Corpus Shopee mới gồm 8 file Markdown và sources.csv.
- [x] Đã chuẩn bị kịch bản demo và phân tích failure cases.
- [x] Push GitHub thành công lên nhánh main ngày 20/09/2026.
- [ ] Nộp link/rating trên vlearn.

Repo dự kiến nộp: https://github.com/hongcuong26-debug/K4-DAY07-NguyenHongCuong-2A202602415
"""
(REPORT / "REPORT_NHOM.md").write_text("\n".join(line.rstrip() for line in group_text.splitlines()) + "\n", encoding="utf-8")
print("Wrote REPORT_CANHAN.md, REPORT_NHOM.md and analysis_stats.json from measured results.")
