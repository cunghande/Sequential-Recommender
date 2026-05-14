# Kien truc he thong

Du an duoc chia thanh bon khoi chinh: `frontend`, `backend`, `ml`, `database`.

## Luong chay tong quan

1. Frontend Next.js hien thi trang san pham, gio hang, profile va For You.
2. Frontend goi FastAPI qua cac ham trong `frontend/lib/api/`.
3. Backend xu ly auth, product, interaction va recommendation qua cac router trong `backend/app/routers/`.
4. Backend doc/ghi MySQL de luu users, products va interactions.
5. Backend nap `model_artifacts.pkl` va `GRU4Rec_best.pt` tu `ml/checkpoints/` de suy luan goi y.

## Backend

- `backend/app/main.py`: khoi tao FastAPI va dang ky router.
- `backend/app/routers/`: endpoint HTTP, moi file phu trach mot nhom nghiep vu.
- `backend/app/schemas/`: Pydantic schema cho request/response.
- `backend/app/services/`: logic nghiep vu, goi database va model.
- `backend/app/db/`: ket noi MySQL va query dung chung.
- `backend/app/core/`: cau hinh, bao mat JWT va dependency lay user.

## Frontend

- `frontend/app/`: route chinh cua Next.js App Router.
- `frontend/components/layout/`: header, footer.
- `frontend/components/product/`: card, grid, filter san pham.
- `frontend/components/recommendation/`: section For You/goi y.
- `frontend/components/user/`: avatar/profile UI.
- `frontend/lib/api/`: ham goi API tach theo auth/products/recommendations/interactions.
- `frontend/lib/types/`: type dung chung cho product, user, recommendation.

## ML va Database

- `ml/notebooks/`: notebook train va phan tich du lieu.
- `ml/checkpoints/`: checkpoint model va artifacts dung cho demo.
- `ml/reports/`: metric va hinh anh dua vao bao cao.
- `database/schema.sql`: schema MySQL duoc Docker Compose import.

