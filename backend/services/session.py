"""
In-memory session management thay thế Redis.
Lưu sequence (chuỗi item_id) của từng user trong bộ nhớ.
Dữ liệu sẽ mất khi restart server — phù hợp cho demo realtime.
"""
from collections import defaultdict

MAX_SEQ_LEN = 50

# {user_id: [item_id, item_id, ...]}
_sessions: dict[str, list] = defaultdict(list)

def get_sequence(user_id: str) -> list:
    """Lấy chuỗi item_id của user từ bộ nhớ."""
    return list(_sessions[str(user_id)])

def add_to_sequence(user_id: str, item_id: int) -> list:
    """Thêm item vào cuối sequence, giữ tối đa MAX_SEQ_LEN item."""
    uid = str(user_id)
    _sessions[uid].append(item_id)
    # Trim về MAX_SEQ_LEN
    if len(_sessions[uid]) > MAX_SEQ_LEN:
        _sessions[uid] = _sessions[uid][-MAX_SEQ_LEN:]
    return list(_sessions[uid])

def boost_sequence(user_id: str, item_id: int, times: int = 3) -> list:
    """
    Lặp lại item trong sequence để tăng weight sở thích.
    Dùng khi user rating >= 4.
    """
    uid = str(user_id)
    for _ in range(times):
        _sessions[uid].append(item_id)
    if len(_sessions[uid]) > MAX_SEQ_LEN:
        _sessions[uid] = _sessions[uid][-MAX_SEQ_LEN:]
    return list(_sessions[uid])

def init_sequence(user_id: str, history: list) -> None:
    """
    Khởi tạo sequence từ lịch sử DB khi user mới đăng nhập.
    Chỉ ghi đè nếu session chưa có.
    """
    uid = str(user_id)
    if not _sessions[uid]:
        _sessions[uid] = list(history[-MAX_SEQ_LEN:])

def remove_from_sequence(user_id: str, item_id: int) -> list:
    """Xóa tất cả lần xuất hiện của item_id khỏi sequence."""
    uid = str(user_id)
    _sessions[uid] = [i for i in _sessions[uid] if i != item_id]
    return list(_sessions[uid])

def clear_sequence(user_id: str) -> None:
    """Xóa sequence khi user logout."""
    uid = str(user_id)
    if uid in _sessions:
        del _sessions[uid]
