# E-commerce Sequential Product Recommendation Platform

Dự án Đồ Án 2 AI: Xây dựng nền tảng thương mại điện tử tích hợp hệ thống gợi ý sản phẩm theo chuỗi thời gian (Sequential Product Recommendation).

## 1. Giới thiệu bài toán
Trong thương mại điện tử hiện đại, việc gợi ý sản phẩm phù hợp với ngữ cảnh và nhu cầu hiện tại của người dùng là vô cùng quan trọng. Bài toán Sequential Product Recommendation tập trung vào việc dự đoán sản phẩm tiếp theo mà người dùng có khả năng tương tác (xem, thêm vào giỏ, mua) dựa trên chuỗi các sản phẩm họ đã tương tác trong quá khứ.
Thay vì chỉ dựa trên sở thích tĩnh, hệ thống này nắm bắt được sự thay đổi linh hoạt trong ý định mua sắm của người dùng theo thời gian thực (Real-time).

## 2. Bộ dữ liệu (Dataset)
Dự án sử dụng bộ dữ liệu **Amazon Beauty** (được trích xuất từ Amazon Product Data).
- **Mô tả:** Bộ dữ liệu chứa thông tin về các sản phẩm làm đẹp, bao gồm lịch sử đánh giá, lượt xem và thông tin chi tiết sản phẩm.
- **Xử lý:** Dữ liệu được tiền xử lý để trích xuất các chuỗi tương tác (interaction sequences) của từng người dùng, được sắp xếp theo trình tự thời gian.

## 3. Các mô hình sử dụng
Hệ thống thử nghiệm và triển khai các mô hình Deep Learning chuyên dụng cho chuỗi:
1. **LSTM (Long Short-Term Memory):** Mô hình Recurrent Neural Network truyền thống giúp nắm bắt sự phụ thuộc xa trong chuỗi tương tác.
2. **GRU4Rec (Gated Recurrent Unit for Recommendation):** Biến thể tối ưu hóa của RNN, đặc biệt hiệu quả trong bài toán Session-based / Sequential Recommendation nhờ cơ chế cổng (gate) đơn giản hơn LSTM nhưng vẫn giữ được thông tin quan trọng.

## 4. Kết quả đánh giá
Kết quả huấn luyện trên tập dữ liệu kiểm thử (Test set):
- **LSTM:**
  - HR@10 (Hit Ratio): `0.5459`
  - NDCG@10 (Normalized Discounted Cumulative Gain): `0.3359`
- **GRU4Rec:**
  - HR@10 (Hit Ratio): `0.5484`
  - NDCG@10 (Normalized Discounted Cumulative Gain): `0.3370`

*Mô hình GRU4Rec cho hiệu suất tốt hơn một chút và được chọn làm mô hình chính để suy luận (inference) trên Backend.*

## 5. Hướng dẫn cài đặt và chạy dự án

### Yêu cầu môi trường
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Docker & Docker Compose (Nếu muốn chạy bằng Docker)

### Cấu hình biến môi trường
Mật khẩu và cấu hình Database được bảo mật thông qua file `.env`. Trong thư mục `backend/` đã có file `.env` mẫu:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=cunghande
DB_NAME=recommendation_db
```

### Cách 1: Chạy bằng Docker (Khuyên dùng)
Dự án đã được cấu hình sẵn `docker-compose.yml` bao gồm Frontend, Backend và Database MySQL.
```bash
# Xây dựng và khởi chạy tất cả các services
docker-compose up -d --build
```
- Frontend (Next.js): http://localhost:3000
- Backend (FastAPI): http://localhost:8000
- Database tự động import schema từ thư mục `data/`

### Cách 2: Chạy thủ công

#### Bước 1: Khởi tạo Database
1. Mở MySQL và tạo database `recommendation_db`.
2. Import schema và data từ các file `data/database.sql` và `data/migrate_v2.sql`.

#### Bước 2: Chạy Backend (FastAPI)
```bash
# 1. Kích hoạt môi trường ảo
.\.venv\Scripts\activate

# 2. Cài đặt thư viện
cd backend
pip install -r requirements.txt

# 3. Chạy server
uvicorn main:app --reload
```
Server chạy tại: `http://127.0.0.1:8000`

#### Bước 3: Chạy Frontend (Next.js)
Mở một Terminal khác:
```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt thư viện
npm install

# 3. Chạy server
npm run dev
```
Trang web chạy tại: `http://localhost:3000`
