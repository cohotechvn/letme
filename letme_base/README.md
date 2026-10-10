# COHOTECH Base (`letme_base`)

## Vai trò COHOTECH

Cài đặt › Người dùng › chọn người › mục **COHOTECH › Vai trò COHOTECH**. Mỗi người một vai trò; vai trò chỉ cộng thêm các quyền chuẩn bên dưới, không bớt quyền đã có.

| Vai trò | Quyền được cộng |
|---|---|
| Nhân viên bán hàng | Bán hàng (đơn của mình), POS người dùng, Kho người dùng, Chỉ đơn bán của mình |
| Kỹ thuật viên | Giống nhân viên bán hàng (Sửa chữa đi theo quyền Kho) |
| Thủ kho kiêm mua hàng | Kho người dùng, Mua hàng người dùng |
| Kế toán | Kế toán quản trị, Chấm công quản lý, Nghỉ phép quản lý |
| Quản lý cửa hàng | Bán hàng quản trị, POS quản lý, Kho quản trị, Mua hàng người dùng, Hoá đơn, Chấm công và Nghỉ phép người duyệt |
| Giám đốc | Quản trị các app Bán hàng, POS, Kho, Mua hàng, Kế toán, Nhân sự, Chấm công, Nghỉ phép |

Quyền Cài đặt (Settings) không nằm trong vai trò nào, vẫn chỉ cấp cho `admin`.

## Chỉ đơn bán của mình

Người có nhóm **Chỉ đơn bán của mình** (vai trò Nhân viên bán hàng, Kỹ thuật viên tự có) chỉ xem, sửa, xoá được đơn bán do mình phụ trách hoặc chưa gán người. Quyền Kho và POS không còn mở đơn của người khác. Người có quyền Bán hàng "Tất cả tài liệu" trở lên không bị giới hạn. Phiếu xuất kho của đơn người khác vẫn mở được.

## Chặn trùng số điện thoại

Khi lưu khách hàng, nếu số điện thoại (bỏ khoảng trắng, dấu chấm, đổi `+84` thành `0`) đã có ở khách khác thì báo lỗi kèm tên khách đó. Các liên hệ thuộc cùng một công ty được dùng chung số. Khách đã lưu trữ không tính. Dữ liệu cũ bị trùng không bị sửa, chỉ chặn khi sửa hoặc tạo mới.

## Khoá sổ theo tháng

Kế toán › Kế toán › Đóng sổ › **Khoá sổ theo tháng** (chỉ Kế toán quản trị). Chọn tháng, năm, loại khoá (bán hàng, mua hàng, kê khai thuế, toàn bộ bút toán); ngày khoá là ngày cuối tháng. Muốn lùi ngày khoá phải tích "Mở lại kỳ đã khoá". Mỗi lần khoá được ghi vào lịch sử của công ty. Khoá cứng (hard lock) không làm ở đây vì không mở lại được.
