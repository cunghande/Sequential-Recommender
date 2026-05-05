import mysql.connector
from mysql.connector import pooling

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'cunghande',
    'database': 'recommendation_db'
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
