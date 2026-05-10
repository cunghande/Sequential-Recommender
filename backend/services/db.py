import mysql.connector
from mysql.connector import pooling

import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'cunghande'),
    'database': os.getenv('DB_NAME', 'recommendation_db')
}

# Connection pool để tránh mở/đóng kết nối liên tục
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="seqrec_pool",
            pool_size=5,
            **DB_CONFIG
        )
    return _pool

def get_connection():
    return get_pool().get_connection()
