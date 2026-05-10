import os
import pickle
import torch
import mysql.connector
from backend.models.gru4rec import GRU4Rec
from backend.services.db import get_connection
from backend.services import session as sess_mgr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class RecommenderService:
    def __init__(self):
        self.artifacts = {}
        self.rich_metadata = {}   # asin → product dict
        self.cfg = {}
        self.meta = {}            # fallback metadata từ checkpoint
        self.id2item = {}         # item_id → asin
        self.item2id = {}         # asin → item_id
        self.train_data = {}
        self.popular_cache = []   # cache top popular items
        self.model = None
        self._load_data()
        self._load_model()

    # ── Boot ────────────────────────────────────────────────────────────────
    def _load_data(self):
        try:
            with open(os.path.join(CHECKPOINT_DIR, 'model_artifacts.pkl'), 'rb') as f:
                self.artifacts = pickle.load(f)

            self._load_metadata_from_db()

            self.cfg       = self.artifacts.get('config', {})
            self.meta      = self.artifacts.get('mappings', {}).get('meta', {})
            self.id2item   = self.artifacts.get('mappings', {}).get('id2item', {})
            self.item2id   = {v: k for k, v in self.id2item.items()}
            self.train_data = self.artifacts.get('sequences', {}).get('train', {})
        except Exception as e:
            print(f"[ERROR] Error loading data: {e}")

    def _load_metadata_from_db(self):
        try:
            conn = get_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT product_id as asin, title, category, price, image_url as img_url FROM products"
                )
                rows = cursor.fetchall()
                self.rich_metadata = {r['asin']: r for r in rows}
                cursor.close()
            finally:
                conn.close()
            print(f"[OK] Loaded {len(self.rich_metadata)} products from MySQL.")
        except Exception as e:
            print(f"[ERROR] Không thể kết nối MySQL: {e}")
            self.rich_metadata = {}

    def _load_model(self):
        try:
            self.model = GRU4Rec(
                self.cfg.get('num_items', 1000),
                self.cfg.get('emb_dim', 64),
                self.cfg.get('hidden', 128),
                self.cfg.get('n_layers', 1),
                self.cfg.get('dropout', 0.2)
            ).to(DEVICE)
            model_path = os.path.join(CHECKPOINT_DIR, 'GRU4Rec_final.pt')
            if os.path.exists(model_path):
                self.model.load_state_dict(
                    torch.load(model_path, map_location=DEVICE, weights_only=True)
                )
                self.model.eval()
                print(f"[OK] Model loaded. Num items: {self.cfg.get('num_items')}")
            else:
                print(f"[WARNING] Model file not found at {model_path}")
        except Exception as e:
            print(f"[ERROR] Error loading model: {e}")

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _enrich(self, item_id: int, score: float = 0.0) -> dict:
        """Chuyển item_id → dict thông tin đầy đủ để trả về API."""
        asin = self.id2item.get(item_id, '?')
        m = self.rich_metadata.get(asin, self.meta.get(asin, {}))
        return {
            "item_id": item_id,
            "asin": asin,
            "title": m.get('title', f'Sản phẩm {item_id}'),
            "category": m.get('category', 'General'),
            "price": float(m.get('price', 0.0) or 0.0),
            "rating": float(m.get('avg_rating', m.get('rating', 0.0)) or 0.0),
            "img_url": m.get('img_url', m.get('image_url', '')),
            "score": round(float(score), 4)
        }

    def _predict(self, hist: list, top_k: int) -> list:
        """Gọi model dự đoán từ chuỗi item_id."""
        if not self.model or not hist:
            return []
        hist = [i for i in hist if i > 0]
        max_len = self.cfg.get('max_len', 50)
        hist = hist[-max_len:]
        seq_len = len(hist)
        if seq_len == 0:
            return []
        padded = [0] * (max_len - seq_len) + hist
        item_seq = torch.tensor([padded], dtype=torch.long).to(DEVICE)
        sl = torch.tensor([seq_len], dtype=torch.long).to(DEVICE)
        top_ids, top_scores = self.model.predict_topk(item_seq, sl, top_k=top_k, exclude_ids=hist)
        return [self._enrich(iid, sc) for iid, sc in zip(top_ids, top_scores)]

    # ── Public API ───────────────────────────────────────────────────────────
    def get_popular_products(self, top_k: int = 12) -> list:
        """
        Trả về sản phẩm phổ biến nhất dựa trên số lượt xem trong bảng interactions.
        Có cache để không query DB liên tục.
        """
        if self.popular_cache:
            return self.popular_cache[:top_k]
        try:
            conn = get_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT i.product_id,
                           SUM(CASE
                               WHEN i.action_type = 'purchase' THEN 5
                               WHEN i.action_type = 'cart' THEN 3
                               WHEN i.action_type = 'rate' AND COALESCE(i.rating, 0) >= 4 THEN 4
                               WHEN i.action_type = 'like' THEN 4
                               ELSE 1
                           END) as popularity_score
                    FROM interactions i
                    WHERE i.action_type IN ('view', 'cart', 'purchase', 'like', 'rate')
                    GROUP BY i.product_id
                    ORDER BY popularity_score DESC
                    LIMIT %s
                """, (top_k * 2,))
                rows = cursor.fetchall()
                cursor.close()
            finally:
                conn.close()

            result = []
            for row in rows:
                asin = row['product_id']
                item_id = self.item2id.get(asin, -1)
                if item_id >= 0:
                    result.append(self._enrich(item_id, score=0.0))
                if len(result) >= top_k:
                    break

            # Nếu không đủ thì lấy từ train_data
            if len(result) < top_k:
                from collections import Counter
                cnt = Counter()
                for seq in list(self.train_data.values())[:500]:
                    cnt.update(seq)
                for iid, _ in cnt.most_common(top_k + len(result)):
                    if len(result) >= top_k:
                        break
                    if iid not in [r['item_id'] for r in result]:
                        result.append(self._enrich(iid, 0.0))

            self.popular_cache = result
            return result[:top_k]
        except Exception as e:
            print(f"[ERROR] get_popular_products: {e}")
            return []

    def get_user_history_from_db(self, user_id: str) -> list:
        """Lấy lịch sử interaction của user từ MySQL (item_id list)."""
        try:
            conn = get_connection()
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT i.product_id
                    FROM interactions i
                    WHERE i.user_id = %s AND i.action_type IN ('view', 'cart', 'purchase', 'like', 'rate')
                    ORDER BY i.timestamp DESC
                    LIMIT 50
                """, (str(user_id),))
                rows = cursor.fetchall()
                cursor.close()
            finally:
                conn.close()
            ids = []
            for row in rows:
                asin = row['product_id']
                iid = self.item2id.get(asin, -1)
                if iid >= 0:
                    ids.append(iid)
            return list(reversed(ids))  # chronological order
        except Exception as e:
            print(f"[ERROR] get_user_history_from_db: {e}")
            return []

    def get_recommendations_for_user(self, user_id: str, top_k: int = 12) -> dict:
        """
        Luồng gợi ý đầy đủ:
        1. Lấy sequence từ in-memory session
        2. Nếu không có → lấy từ DB và khởi tạo session
        3. Nếu vẫn không có → trả popular
        """
        seq = sess_mgr.get_sequence(user_id)

        if not seq:
            db_hist = self.get_user_history_from_db(user_id)
            if db_hist:
                sess_mgr.init_sequence(user_id, db_hist)
                seq = db_hist
            # Nếu vẫn trống → train_data fallback
            if not seq:
                u_key = int(user_id) if str(user_id).isdigit() else user_id
                seq = self.train_data.get(u_key, [])

        if not seq:
            return {"source": "popular", "recommendations": self.get_popular_products(top_k)}

        recs = self._predict(seq, top_k)
        return {"source": "personalized", "recommendations": recs}

    def get_recommendations(self, sequence_history: list, top_k: int = 10) -> list:
        """API cũ: nhận trực tiếp sequence, trả recommendations. Dùng cho realtime demo."""
        return self._predict(sequence_history, top_k)

    def get_user_history(self, user_id: str) -> list | None:
        """Lịch sử hiển thị (có thông tin sản phẩm đầy đủ).
        Kết hợp: train_data (cũ) + DB interactions + session (realtime).
        """
        u_key = int(user_id) if str(user_id).isdigit() else user_id

        # Thu thập từ nhiều nguồn
        train_hist = list(self.train_data.get(u_key, []))
        db_hist = self.get_user_history_from_db(user_id)
        session_hist = sess_mgr.get_sequence(user_id)

        # Merge: train_data → DB → session (ưu tiên mới nhất)
        seen = set()
        merged = []
        # Duyệt ngược ưu tiên: session > DB > train_data
        for iid in reversed(session_hist + db_hist):
            if iid not in seen and iid > 0:
                seen.add(iid)
                merged.append(iid)
        for iid in reversed(train_hist):
            if iid not in seen and iid > 0:
                seen.add(iid)
                merged.append(iid)

        merged = list(reversed(merged))  # chronological order

        if not merged:
            return None

        items_info = []
        for iid in merged[-15:]:
            asin = self.id2item.get(iid, '?')
            m = self.rich_metadata.get(asin, self.meta.get(asin, {}))
            items_info.append({
                "item_id": iid,
                "asin": asin,
                "title": m.get('title', f'ID: {iid}'),
                "img_url": m.get('img_url', m.get('image_url', ''))
            })
        return items_info

    def record_interaction(self, user_id: str, product_asin: str, action_type: str, rating: float = None):
        """
        Lưu interaction vào DB và cập nhật session trong bộ nhớ.
        Trả về danh sách recommendations mới.
        """
        # 1. Lưu vào DB
        try:
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO interactions (user_id, product_id, action_type, rating) VALUES (%s, %s, %s, %s)",
                    (str(user_id), product_asin, action_type, rating)
                )
                conn.commit()
                cursor.close()
            finally:
                conn.close()
        except Exception as e:
            print(f"[ERROR] record_interaction DB: {e}")

        # 2. Cập nhật session
        item_id = self.item2id.get(product_asin, -1)
        if item_id >= 0:
            if action_type in ('purchase', 'like') or (rating and rating >= 4):
                sess_mgr.boost_sequence(user_id, item_id, times=3)
            elif action_type == 'cart':
                sess_mgr.boost_sequence(user_id, item_id, times=2)
            else:
                sess_mgr.add_to_sequence(user_id, item_id)

        # 3. Predict mới ngay
        result = self.get_recommendations_for_user(user_id, top_k=12)
        return result

    def get_product_detail(self, asin: str) -> dict | None:
        """Lấy thông tin chi tiết sản phẩm từ metadata."""
        m = self.rich_metadata.get(asin)
        if not m:
            return None
        item_id = self.item2id.get(asin, -1)
        return self._enrich(item_id, 0.0)

    def delete_interaction(self, user_id: str, product_asin: str) -> dict:
        """
        Xóa tất cả interaction của user với product_asin khỏi DB và session.
        Trả về history mới và recommendations mới.
        """
        # 1. Xóa khỏi DB
        try:
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM interactions WHERE user_id = %s AND product_id = %s",
                    (str(user_id), product_asin)
                )
                conn.commit()
                cursor.close()
            finally:
                conn.close()
        except Exception as e:
            print(f"[ERROR] delete_interaction DB: {e}")

        # 2. Xóa khỏi session
        item_id = self.item2id.get(product_asin, -1)
        if item_id >= 0:
            sess_mgr.remove_from_sequence(user_id, item_id)

        # 3. Trả về kết quả mới
        new_history = self.get_user_history(user_id)
        new_recs = self.get_recommendations_for_user(user_id, top_k=12)
        return {
            "history": new_history or [],
            "recommendations": new_recs.get("recommendations", []),
            "source": new_recs.get("source", "popular")
        }

    def get_stats(self):
        return self.artifacts.get('results', {"HR_10": 0.198, "NDCG_10": 0.105})

    def invalidate_popular_cache(self):
        self.popular_cache = []


recommender_service = RecommenderService()
