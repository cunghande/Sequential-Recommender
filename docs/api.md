# API chinh

Backend chay bang FastAPI, entrypoint moi la `backend.app.main:app`.

## Auth

- `POST /auth/register`: dang ky user moi.
- `POST /auth/login`: dang nhap bang email hoac user_id.
- `GET /auth/me`: lay user hien tai tu JWT.
- `PUT /auth/profile`: cap nhat ten hien thi/avatar.
- `POST /auth/change-password`: doi mat khau.
- `POST /auth/logout`: xoa session goi y tam thoi.

## Products

- `GET /products`: danh sach san pham, ho tro `category`, `search`, `page`, `limit`.
- `GET /products/categories`: danh sach loai hang.
- `GET /products/{asin}`: chi tiet mot san pham.

## Interactions

- `POST /interaction`: luu hanh vi `view`, `cart`, `purchase`, `like`, `rate`.
- Backend cap nhat session va cache popular sau khi ghi interaction.

## Recommendations

- `GET /recommend`: goi y cho user hien tai, demo user, hoac popular neu user moi.
- `GET /recommend/popular`: san pham pho bien cho cold-start user.
- `POST /recommend/sequence`: goi y realtime tu sequence tam, khong luu DB.
- `POST /recommend`: endpoint legacy cho frontend cu.

## Users

- `GET /users/{user_id}/history`: lay lich su tuong tac.
- `DELETE /users/{user_id}/history/{product_asin}`: xoa mot item khoi lich su.

