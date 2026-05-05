-- Thêm các cột mới vào bảng users nếu chưa có (chạy lần đầu khi migrate)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS full_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS avatar_url TEXT,
    ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS reset_token_expires DATETIME NULL;

-- Thêm avg_rating vào bảng products nếu chưa có
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS avg_rating FLOAT DEFAULT 0;
