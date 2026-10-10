# letme

Module Odoo 20 Community riêng của COHOTECH. Mọi module dùng tiền tố `letme_`, model dùng tiền tố `letme.`.

## Cài vào Odoo đang chạy bằng Docker

1. Chép thư mục module (ví dụ `letme_base`) vào `C:\cohotech-odoo20\custom-addons\`, thư mục này được gắn vào container ở `/mnt/extra-addons`.
2. Sao lưu cơ sở dữ liệu trước (`scripts\backup-cohotech.ps1`).
3. Cài hoặc cập nhật module:

   ```
   docker compose stop odoo
   docker compose run --rm odoo odoo -d cohotech -i letme_base --stop-after-init
   docker compose start odoo
   ```

   Khi cập nhật bản mới thì thay `-i` bằng `-u`.

## Quy ước

- Mỗi thay đổi đi qua một pull request, không đẩy thẳng vào `main`.
- Tên biến, tên hàm, commit viết bằng tiếng Anh; giao diện có bản dịch `i18n/vi.po`.
- Phân quyền theo chuẩn Odoo 20: `security/ir.access.csv` (thay cho `ir.model.access.csv` và `ir.rule`).

## Danh sách module

| Module | Nội dung |
|---|---|
| `letme_base` | Vai trò COHOTECH, chỉ xem đơn của mình, chặn trùng số điện thoại khách, khoá sổ theo tháng |
