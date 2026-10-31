# COHOTECH SEO (`letme_seo`)

Bổ sung những phần SEO mà Odoo 20 Community chưa có. Những gì Odoo đã làm tốt (tiêu đề, mô tả, Open Graph, canonical, hreflang, sitemap, robots.txt, llms.txt, chuyển hướng 301/302, JSON-LD cho sản phẩm, blog, sự kiện) giữ nguyên, module chỉ cộng thêm.

Chỉ phụ thuộc `website`. Khi có Bán hàng online, Blog, Sự kiện thì sản phẩm, danh mục, bài viết, sự kiện tự được đưa vào kiểm tra.

## Kiểm tra SEO

Website › Báo cáo › SEO › **Kiểm tra SEO**, bấm **Chạy kiểm tra** (tự chạy mỗi ngày). Kiểm tra mọi trang, sản phẩm, danh mục, bài viết, sự kiện đang đăng trên từng website, theo ngôn ngữ mặc định của website:

| Lỗi | Mức độ | Ngưỡng |
|---|---|---|
| Thiếu mô tả meta | Cao | Không có mô tả, kể cả mô tả mặc định (mô tả bán hàng, phụ đề) |
| Mô tả quá ngắn / quá dài | Trung bình / Thấp | Dưới 70 / trên 160 ký tự |
| Tiêu đề quá dài / quá ngắn | Trung bình / Thấp | Trên 60 / dưới 15 ký tự, tính cả đuôi " \| tên website" |
| Tiêu đề, mô tả trùng nhau | Trung bình | Trùng giữa các trang của cùng website |
| Không có hoặc nhiều Heading 1 | Trung bình / Thấp | Chỉ với trang tĩnh |
| Ảnh thiếu alt | Thấp | Ảnh không có thuộc tính alt trong nội dung |
| Trang đang đăng nhưng ẩn khỏi Google | Thấp | Trang tắt "Được lập chỉ mục" |
| Cài đặt website | Cao đến Thấp | Chưa đặt tên miền, chưa xác minh Google/Bing, chưa có Analytics, chưa có ảnh chia sẻ, doanh nghiệp địa phương thiếu địa chỉ |

Chọn các dòng rồi bấm **Tự điền thẻ meta**: thiếu mô tả thì lấy mô tả bán hàng, phụ đề hoặc các đoạn văn của trang, cắt gọn dưới 155 ký tự đúng ranh giới từ; tiêu đề quá dài thì đặt tiêu đề meta là tên trang cắt dưới 60 ký tự. Nên đọc lại nội dung tự điền trước khi chạy cho hàng loạt.

## Nhật ký lỗi 404

Website › Báo cáo › SEO › **Lỗi 404**. Mỗi URL trả về "không tìm thấy trang" được ghi một dòng, có số lượt, lần đầu, lần cuối, trang dẫn tới và trình duyệt. Bấm **Chuyển hướng** để tạo chuyển hướng 301 có sẵn URL nguồn; khi đã có chuyển hướng, dòng tự sang "Đã chuyển hướng". **Bỏ qua** để ẩn URL không cần xử lý.

- Không ghi đường dẫn kỹ thuật và URL dò lỗ hổng (`/web/*`, `/static/*`, `*.php`, `/wp-*`, `*.env`...). Đổi danh sách bằng tham số hệ thống `letme_seo.not_found_ignore_patterns`, mỗi dòng một mẫu kiểu `*.php`.
- Ghi bằng giao dịch riêng nên không làm chậm hay hỏng trang 404 của khách.
- URL không ai truy cập lại trong 90 ngày tự xoá.

## Cài đặt

Website › Cấu hình › Cài đặt › mục **Tracking & SEO**:

- **Xác minh công cụ tìm kiếm**: dán mã của Google, Bing, Yandex, Facebook, Zalo. Module thêm thẻ meta tương ứng vào `<head>` mọi trang.
- **Thông tin doanh nghiệp cho Google**: chọn loại hình (Tổ chức, Doanh nghiệp địa phương, Cửa hàng điện tử, Cửa hàng điện thoại...), giờ mở cửa, khoảng giá. Dữ liệu JSON-LD trên mọi trang thêm điện thoại, email, địa chỉ, mã số thuế, mạng xã hội của công ty, và thêm thực thể `WebSite` để Google hiện đúng tên website.
- **Xem trước ảnh lớn**: thêm `max-image-preview:large` cho các trang được lập chỉ mục (bật sẵn).
