# Do An 2 AI Project - Sequential Product Recommendation

Website thương mại điện tử sản phẩm game tích hợp hệ thống gợi ý sản phẩm theo chuỗi hành vi người dùng. Dự án kết hợp Next.js, FastAPI, MySQL và mô hình GRU4Rec/LSTM để minh họa đầy đủ quy trình xây dựng một hệ thống phần mềm AI: thu thập dữ liệu, tiền xử lý, quan sát dữ liệu, huấn luyện mô hình, đánh giá, triển khai và demo.

## 1. Giới thiệu bài toán

Trong website thương mại điện tử, người dùng thường tương tác với nhiều sản phẩm theo trình tự thời gian: xem sản phẩm, thêm vào giỏ hàng, yêu thích, đánh giá hoặc mua hàng. Bài toán của dự án là dự đoán sản phẩm tiếp theo mà người dùng có khả năng quan tâm dựa trên chuỗi hành vi trước đó.

Hệ thống xử lý hai trường hợp chính:

- **User mới hoặc chưa có lịch sử:** gợi ý các sản phẩm phổ biến dựa trên lượt xem, thêm giỏ hàng, yêu thích, đánh giá cao và mua hàng.
- **User đã có lịch sử:** dùng chuỗi sản phẩm đã tương tác để gợi ý các sản phẩm tương tự bằng mô hình tuần tự GRU4Rec.

## 2. Bộ dữ liệu

Dự án sử dụng tập dữ liệu **Amazon Reviews 2023 - Video Games** của McAuley Lab.

- Trang dataset chính thức: https://amazon-reviews-2023.github.io/
- Review data: https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Video_Games.jsonl.gz
- Metadata sản phẩm: https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/meta_categories/meta_Video_Games.jsonl.gz

Các trường chính được sử dụng:

- `user_id`: mã người dùng.
- `parent_asin` hoặc `asin`: mã sản phẩm.
- `rating`: điểm đánh giá từ 1 đến 5.
- `timestamp`: thời gian tương tác.
- `title`, `category`, `price`, `average_rating`, `images`: thông tin hiển thị sản phẩm.

Thống kê dữ liệu gốc trong notebook:

| Chỉ số | Giá trị |
| --- | ---: |
| Interactions | 4,624,615 |
| Users | 2,766,656 |
| Items | 137,249 |
| Avg rating | 4.05 |
| Sparsity | 99.9988% |
| Time range | 1998-11-17 đến 2023-09-12 |

## 3. Quy trình tiền xử lý dữ liệu

Notebook chính nằm tại `ml/notebooks/seqrec_training_pipeline.ipynb`.

Các bước tiền xử lý:

1. Đọc review và metadata từ file JSONL.
2. Chuẩn hóa cột `user_id`, `item_id`, `rating`, `timestamp`.
3. Ghép metadata sản phẩm như title, category, price, image.
4. Quan sát dữ liệu bằng phân phối rating, độ dài sequence, top category và top product.
5. Lọc k-core với `K_CORE=5` để giữ user/item có đủ tương tác.
6. Encode user/item sang id số, dùng `0` làm padding.
7. Sắp xếp interaction theo thời gian.
8. Tạo sequence sản phẩm theo từng user.
9. Chia dữ liệu theo leave-one-out:
   - Train: toàn bộ lịch sử trừ 2 item cuối.
   - Validation: item kế cuối.
   - Test: item cuối.
10. Đánh giá bằng 1 positive item và 99 negative items.

Sau k-core:

| Chỉ số | Giá trị |
| --- | ---: |
| Users | 98,906 |
| Items | 26,354 |
| Max sequence length | 50 |
| Negative samples | 99 |

## 4. Mô hình sử dụng

### Item-KNN Baseline

Item-KNN là mô hình baseline dựa trên độ tương đồng cosine giữa các sản phẩm. Mô hình này giúp so sánh xem các mô hình tuần tự có cải thiện so với collaborative filtering truyền thống hay không.

### LSTM

LSTM là mô hình recurrent neural network có khả năng học phụ thuộc dài hạn trong chuỗi tương tác. Trong dự án, LSTM nhận sequence sản phẩm đã padding và dự đoán item tiếp theo.

### GRU4Rec

GRU4Rec là mô hình chính dùng cho demo. GRU có ít tham số hơn LSTM, hội tụ nhanh hơn và phù hợp với bài toán session-based/sequential recommendation.

## 5. Kết quả đánh giá

Metric sử dụng:

- `HR@K`: kiểm tra item đúng có nằm trong top K gợi ý hay không.
- `NDCG@K`: đánh giá thứ hạng của item đúng trong top K, item đúng càng cao điểm càng tốt.

Kết quả test từ notebook:

| Mô hình | HR@5 | HR@10 | HR@20 | NDCG@5 | NDCG@10 | NDCG@20 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Item-KNN | 0.1378 | 0.1378 | 0.1378 | 0.1330 | 0.1330 | 0.1330 |
| LSTM | 0.3686 | 0.4997 | 0.6412 | 0.2607 | 0.3031 | 0.3388 |
| GRU4Rec | 0.3715 | 0.5046 | 0.6467 | 0.2628 | 0.3059 | 0.3418 |

Trong quá trình validation, GRU4Rec đạt mốc tốt nhất:

| Mô hình | Best Val HR@10 | Best Val NDCG@10 |
| --- | ---: | ---: |
| LSTM | 0.5459 | 0.3359 |
| GRU4Rec | 0.5484 | 0.3370 |

GRU4Rec được chọn làm mô hình chính cho backend inference vì có kết quả tốt nhất và tốc độ suy luận phù hợp cho demo.

## 6. Chức năng hệ thống demo

- Đăng ký, đăng nhập, đăng xuất.
- Cập nhật profile, avatar, đổi mật khẩu.
- Danh sách sản phẩm có tìm kiếm, lọc category và phân trang.
- Trang chi tiết sản phẩm.
- Giỏ hàng.
- Yêu thích sản phẩm.
- Lịch sử xem sản phẩm.
- Xóa sản phẩm khỏi lịch sử.
- Ghi nhận hành vi `view`, `cart`, `purchase`, `like`, `rate`.
- Trang For You:
  - User mới: gợi ý popular products.
  - User cũ: gợi ý personalized bằng GRU4Rec.

## 7. Cấu trúc dự án

```text
Project_Root/
├── backend/
│   ├── app/
│   │   ├── core/          # Cấu hình, JWT, dependency
│   │   ├── db/            # Kết nối và query MySQL
│   │   ├── models/        # Model AI phục vụ inference
│   │   ├── routers/       # API endpoints theo từng nhóm nghiệp vụ
│   │   ├── schemas/       # Pydantic request/response schema
│   │   ├── services/      # Logic nghiệp vụ
│   │   └── main.py        # FastAPI app mới
│   ├── services/          # Service lõi và shim tương thích
│   └── requirements.txt
├── frontend/
│   ├── app/               # Next.js App Router pages
│   ├── components/        # UI components
│   ├── lib/api/           # API client tách theo nghiệp vụ
│   ├── lib/types/         # TypeScript shared types
│   └── public/
├── ml/
│   ├── notebooks/         # Notebook train và EDA
│   ├── checkpoints/       # GRU4Rec/LSTM weights và artifacts
│   └── reports/           # Metrics, logs, figures
├── database/
│   └── schema.sql         # MySQL schema
├── docs/                  # Tài liệu kiến trúc, API, pipeline
└── docker-compose.yml
```

## 8. Cài đặt và chạy dự án

### Yêu cầu

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Docker Desktop nếu chạy bằng Docker Compose

### Cấu hình backend

Tạo file `backend/.env` dựa trên `backend/.env.example`:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
JWT_SECRET=change-this-secret
JWT_EXPIRE_HOURS=24
FRONTEND_URL=http://localhost:3000
GMAIL_ADDRESS=
GMAIL_APP_PASS=
```

### Chạy bằng Docker

```bash
docker-compose up -d --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### Chạy thủ công

Backend:

```bash
cd D:/Project_Root
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8001
```

Frontend:

```bash
cd D:/Project_Root/frontend
npm install
npm run dev
```

## 9. Tài liệu bổ sung

- `docs/architecture.md`: kiến trúc hệ thống.
- `docs/api.md`: danh sách API.
- `docs/recommendation_pipeline.md`: pipeline AI.
- `docs/report_notes.md`: ghi chú kết quả để viết báo cáo.

## 10. Tác giả

**Cungdo**  
Email: **docung926@gmail.com**
