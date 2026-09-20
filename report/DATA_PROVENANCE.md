# Nhật ký nguồn và giới hạn corpus

Ngày kiểm tra: 20/09/2026. Chủ đề: chính sách trả hàng và hoàn tiền Shopee Việt Nam.

## Phương pháp thực tế

1. Đọc `docs/DATA_COLLECTION.md`, điều khoản dịch vụ và robots trước khi tạo corpus.
2. Truy cập `https://help.shopee.vn/robots.txt` bằng Python urllib với User-Agent
   `Day7DataFoundationsCourse/1.0 (+educational-lab)`. Phản hồi HTTP 200:

   ```text
   User-Agent:*
   Allow: /

   sitemap: https://help.shopee.vn/sitemap.xml
   ```

3. Các lần tải trang bài viết bằng urllib từ máy này bị timeout; không ghi chúng là
   crawl thành công. Công cụ đọc web truy cập được nội dung HTML công khai của năm
   URL trong `sources.csv`; dùng nội dung đã đọc đó để đối chiếu từng dữ kiện.
   Không đăng nhập, không dùng API nội bộ, không vượt CAPTCHA. Không lấy nội dung
   từ seller.shopee.vn hoặc CDN vì không xác minh được quyền truy cập ở các nguồn đó.
4. [Điều khoản dịch vụ, mục 3](https://help.shopee.vn/portal/4/article/77243)
   không cấp giấy phép mở cho nội dung. Vì vậy repo chỉ chứa **bản ghi kiến thức
   ngắn diễn đạt lại các dữ kiện**, giữ số mục nguồn để tra cứu, không tái bản toàn
   bộ bài viết và không công bố HTML thô. `public-source` chỉ mô tả nguồn công khai,
   không đồng nghĩa Shopee cấp quyền sử dụng mở.
5. Metadata `collection_method: web-read-and-factual-summary` phân biệt rõ các bản
   ghi này với văn bản gốc được crawler trích nguyên văn. Tiêu đề tài liệu do người
   biên soạn đặt; heading giữ hoặc rút gọn mục tương ứng trong nguồn. Nội dung không
   bao gồm menu, form tìm kiếm, banner, video, đánh giá bài viết hoặc thông tin cá nhân.

**Giới hạn cần công khai:** đây là corpus tóm lược có đối chiếu nguồn, không phải
5 bản chính sách nguyên văn đã crawl/clean. Nếu giảng viên yêu cầu đúng loại văn bản
gốc đó, CP2 còn cần thay bằng các trích đoạn được phép sử dụng hoặc nguồn được cấp
phép. Không tự đánh dấu đáp ứng đầy đủ yêu cầu quyền tái sử dụng. Các kết quả benchmark
trong repo chỉ có giá trị cho năm bản ghi thực tế đang lưu.

## Đối chiếu từng nguồn

| File | Bài nguồn | Mục đã đối chiếu | Phiên bản |
|---|---|---|---|
| buyer-dieu-kien | [188931](https://help.shopee.vn/portal/4/article/188931) | 1.1–1.3 | not-stated |
| buyer-gui-hang | [189477](https://help.shopee.vn/portal/4/article/189477) | 1.1, 1.4, 2.2, 3 | not-stated |
| buyer-gui-yeu-cau | [79233](https://help.shopee.vn/portal/4/article/79233) | 1: cách 1 và 2; mục 2 | not-stated |
| buyer-nhan-tien | [189473](https://help.shopee.vn/portal/4/article/189473) | bảng 1 và lưu ý | not-stated |
| seller-phan-hoi | [77251](https://help.shopee.vn/portal/4/article/77251) | 5; 7.2; 12.2 | hiệu lực 11/03/2026 |

Không dùng bài 77491 vì tiêu đề ghi **bản trước đây**. `not-stated` có nghĩa không
có ngày hiệu lực chung xác định cho cả bài; không lấy ngày crawl làm ngày hiệu lực.
Thông tin không phải cam kết rằng Shopee sẽ giữ chính sách này trong tương lai.

## Tái lập và kiểm tra

`python scripts/build_manifest.py` tái tạo inventory, không thu thập lại nội dung.
`python scripts/validate_lab.py` kiểm tra 5 file, metadata, 4 buyer + 1 seller,
manifest 1:1 và sự hiện diện của bằng chứng gold. SHA-256 của file corpus và bộ câu
hỏi được lưu trong JSON benchmark để tránh so sánh hai lần chạy khác dữ liệu.

Q1 cố ý không nói rõ vai trò. Ở bản thử ban đầu dùng buyer, A/B của heading không
thay đổi; cấu hình cuối chốt **seller** để kiểm tra đúng trường hợp phí chiều hoàn
của shop đối lập với ứng phí của khách. Cả ba chiến lược được chạy lại chung cấu
hình cuối. Đây là thiết kế ca thử filter; không dùng sự thay đổi thứ hạng do mock
để khẳng định chất lượng ngữ nghĩa được cải thiện.
