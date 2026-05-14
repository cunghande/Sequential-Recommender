-- =====================================================
-- SeqRec AI — Database Schema v2.0
-- =====================================================
CREATE DATABASE IF NOT EXISTS your_database_name;
USE your_database_name;

-- 1. Bảng Users (có auth + reset password)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    password_hash TEXT,
    avatar_url TEXT,
    reset_token VARCHAR(255) NULL,
    reset_token_expires DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng Products
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    title TEXT,
    category VARCHAR(100),
    price FLOAT,
    brand VARCHAR(100),
    description TEXT,
    image_url TEXT,
    avg_rating FLOAT DEFAULT 0
);

-- 3. Bảng Interactions
CREATE TABLE IF NOT EXISTS interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    product_id VARCHAR(50),
    action_type VARCHAR(20),   -- 'view' | 'rate'
    rating FLOAT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- 4. Indexes để tăng tốc query
CREATE INDEX IF NOT EXISTS idx_user_time ON interactions(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_product_views ON interactions(product_id, action_type);