from collections import Counter
from pathlib import Path
from typing import Any

import pickle
import torch

from backend.models.gru4rec import GRU4Rec
from backend.services import session as session_store
from backend.services.db import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DIRS = [
    PROJECT_ROOT / "ml" / "checkpoints",
    PROJECT_ROOT / "checkpoints",
]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class RecommenderService:
    """Quản lý toàn bộ luồng gợi ý: nạp model, lấy lịch sử, lưu hành vi và suy luận."""

    def __init__(self):
        self.artifacts: dict[str, Any] = {}
        self.rich_metadata: dict[str, dict] = {}
        self.cfg: dict[str, Any] = {}
        self.meta: dict[str, dict] = {}
        self.id2item: dict[int, str] = {}
        self.item2id: dict[str, int] = {}
        self.train_data: dict[Any, list[int]] = {}
        self.popular_cache: list[dict] = []
        self.model: GRU4Rec | None = None

        self._load_artifacts()
        self._load_metadata_from_db()
        self._load_model()

    def _first_existing_file(self, filenames: list[str]) -> Path | None:
        """Tìm file đầu tiên tồn tại trong các thư mục checkpoint ưu tiên."""
        for checkpoint_dir in CHECKPOINT_DIRS:
            for filename in filenames:
                path = checkpoint_dir / filename
                if path.exists():
                    return path
        return None

    def _load_artifacts(self) -> None:
        """Nạp mapping item/user, metadata fallback và lịch sử train từ model_artifacts.pkl."""
        artifact_path = self._first_existing_file(["model_artifacts.pkl"])
        if not artifact_path:
            print("[WARNING] model_artifacts.pkl not found")
            return

        try:
            with artifact_path.open("rb") as file:
                self.artifacts = pickle.load(file)

            mappings = self.artifacts.get("mappings", {})
            self.cfg = self.artifacts.get("config", {})
            self.meta = mappings.get("meta", {})
            self.id2item = mappings.get("id2item", {})
            self.item2id = mappings.get("item2id") or {asin: item_id for item_id, asin in self.id2item.items()}
            self.train_data = self.artifacts.get("sequences", {}).get("train", {})
            print(f"[OK] Loaded artifacts from {artifact_path}")
        except Exception as exc:
            print(f"[ERROR] Error loading artifacts: {exc}")

    def _load_metadata_from_db(self) -> None:
        """Nạp metadata sản phẩm từ MySQL để API trả dữ liệu mới nhất cho frontend."""
        try:
            rows = self._fetch_all(
                "SELECT product_id as asin, title, category, price, image_url as img_url FROM products"
            )
            self.rich_metadata = {row["asin"]: row for row in rows}
            print(f"[OK] Loaded {len(self.rich_metadata)} products from MySQL.")
        except Exception as exc:
            print(f"[ERROR] Cannot connect to MySQL: {exc}")
            self.rich_metadata = {}

    def _load_model(self) -> None:
        """Khởi tạo GRU4Rec và nạp checkpoint tốt nhất để suy luận."""
        model_path = self._first_existing_file(["GRU4Rec_best.pt", "GRU4Rec_final.pt"])
        if not model_path:
            print("[WARNING] GRU4Rec checkpoint not found")
            return

        try:
            self.model = GRU4Rec(
                self.cfg.get("num_items", 1000),
                self.cfg.get("emb_dim", 64),
                self.cfg.get("hidden", 128),
                self.cfg.get("n_layers", 1),
                self.cfg.get("dropout", 0.2),
            ).to(DEVICE)
            self.model.load_state_dict(torch.load(model_path, map_location=DEVICE, weights_only=True))
            self.model.eval()
            print(f"[OK] Model loaded from {model_path}. Num items: {self.cfg.get('num_items')}")
        except Exception as exc:
            self.model = None
            print(f"[ERROR] Error loading model: {exc}")

    def _fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        """Chạy SELECT và trả danh sách dict từ MySQL."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            conn.close()

    def _execute_write(self, query: str, params: tuple) -> None:
        """Chạy INSERT/UPDATE/DELETE và commit thay đổi xuống MySQL."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
        finally:
            conn.close()

    def _metadata_for_asin(self, asin: str) -> dict:
        """Lấy metadata sản phẩm, ưu tiên MySQL và fallback về artifact train."""
        return self.rich_metadata.get(asin) or self.meta.get(asin, {})

    def _enrich(self, item_id: int, score: float = 0.0) -> dict:
        """Chuyển item_id nội bộ thành object sản phẩm đầy đủ cho frontend."""
        asin = self.id2item.get(item_id, "?")
        metadata = self._metadata_for_asin(asin)
        return {
            "item_id": item_id,
            "asin": asin,
            "title": metadata.get("title", f"Sản phẩm {item_id}"),
            "category": metadata.get("category", "General"),
            "price": float(metadata.get("price", 0.0) or 0.0),
            "rating": float(metadata.get("avg_rating", metadata.get("rating", 0.0)) or 0.0),
            "img_url": metadata.get("img_url", metadata.get("image_url", "")),
            "score": round(float(score), 4),
        }

    def _predict(self, history: list[int], top_k: int) -> list[dict]:
        """Dùng GRU4Rec dự đoán top sản phẩm tiếp theo từ chuỗi item_id."""
        if not self.model:
            return []

        history = [item_id for item_id in history if item_id > 0]
        max_len = self.cfg.get("max_len", 50)
        history = history[-max_len:]
        if not history:
            return []

        padded = [0] * (max_len - len(history)) + history
        item_seq = torch.tensor([padded], dtype=torch.long).to(DEVICE)
        seq_len = torch.tensor([len(history)], dtype=torch.long).to(DEVICE)
        top_ids, top_scores = self.model.predict_topk(item_seq, seq_len, top_k=top_k, exclude_ids=history)
        return [self._enrich(item_id, score) for item_id, score in zip(top_ids, top_scores)]

    def _fallback_popular_from_train(self, top_k: int, current_items: list[dict]) -> list[dict]:
        """Bổ sung popular bằng dữ liệu train khi MySQL chưa đủ interactions."""
        selected_ids = {item["item_id"] for item in current_items}
        counter: Counter[int] = Counter()
        for sequence in list(self.train_data.values())[:500]:
            counter.update(sequence)

        result = list(current_items)
        for item_id, _ in counter.most_common(top_k * 2):
            if len(result) >= top_k:
                break
            if item_id not in selected_ids:
                selected_ids.add(item_id)
                result.append(self._enrich(item_id))
        return result

    def get_popular_products(self, top_k: int = 12) -> list[dict]:
        """Lấy sản phẩm phổ biến cho user mới hoặc khi chưa có lịch sử."""
        if self.popular_cache:
            return self.popular_cache[:top_k]

        result: list[dict] = []
        try:
            rows = self._fetch_all(
                """
                SELECT product_id,
                       SUM(CASE
                           WHEN action_type = 'purchase' THEN 5
                           WHEN action_type = 'cart' THEN 3
                           WHEN action_type IN ('like', 'rate') THEN 4
                           ELSE 1
                       END) as popularity_score
                FROM interactions
                WHERE action_type IN ('view', 'cart', 'purchase', 'like', 'rate')
                GROUP BY product_id
                ORDER BY popularity_score DESC
                LIMIT %s
                """,
                (top_k * 2,),
            )
            for row in rows:
                item_id = self.item2id.get(row["product_id"], -1)
                if item_id > 0:
                    result.append(self._enrich(item_id))
                if len(result) >= top_k:
                    break
        except Exception as exc:
            print(f"[ERROR] get_popular_products: {exc}")

        self.popular_cache = self._fallback_popular_from_train(top_k, result)
        return self.popular_cache[:top_k]

    def get_user_history_from_db(self, user_id: str) -> list[int]:
        """Lấy lịch sử tương tác từ MySQL và chuyển ASIN sang item_id nội bộ."""
        try:
            rows = self._fetch_all(
                """
                SELECT product_id
                FROM interactions
                WHERE user_id = %s AND action_type IN ('view', 'cart', 'purchase', 'like', 'rate')
                ORDER BY timestamp DESC
                LIMIT 50
                """,
                (str(user_id),),
            )
        except Exception as exc:
            print(f"[ERROR] get_user_history_from_db: {exc}")
            return []

        history = [self.item2id.get(row["product_id"], -1) for row in rows]
        return [item_id for item_id in reversed(history) if item_id > 0]

    def _sequence_for_user(self, user_id: str) -> list[int]:
        """Ghép lịch sử từ session, database và train_data để tạo chuỗi gợi ý tốt nhất."""
        sequence = session_store.get_sequence(user_id)
        if sequence:
            return sequence

        db_history = self.get_user_history_from_db(user_id)
        if db_history:
            session_store.init_sequence(user_id, db_history)
            return db_history

        train_key: int | str = int(user_id) if str(user_id).isdigit() else user_id
        return list(self.train_data.get(train_key, []))

    def get_recommendations_for_user(self, user_id: str, top_k: int = 12) -> dict:
        """Trả gợi ý cá nhân hóa; nếu user chưa có lịch sử thì trả popular."""
        sequence = self._sequence_for_user(user_id)
        if not sequence:
            return {"source": "popular", "recommendations": self.get_popular_products(top_k)}
        return {"source": "personalized", "recommendations": self._predict(sequence, top_k)}

    def get_recommendations(self, sequence_history: list[int], top_k: int = 10) -> list[dict]:
        """Gợi ý realtime từ sequence truyền trực tiếp, dùng cho endpoint demo."""
        return self._predict(sequence_history, top_k)

    def get_user_history(self, user_id: str) -> list[dict] | None:
        """Trả lịch sử xem/mua/thích có metadata để hiển thị trong profile."""
        train_key: int | str = int(user_id) if str(user_id).isdigit() else user_id
        sources = [
            list(self.train_data.get(train_key, [])),
            self.get_user_history_from_db(user_id),
            session_store.get_sequence(user_id),
        ]

        seen: set[int] = set()
        merged: list[int] = []
        for source in sources:
            for item_id in source:
                if item_id > 0 and item_id not in seen:
                    seen.add(item_id)
                    merged.append(item_id)

        if not merged:
            return None

        return [
            {
                "item_id": item_id,
                "asin": self.id2item.get(item_id, "?"),
                "title": self._metadata_for_asin(self.id2item.get(item_id, "?")).get("title", f"ID: {item_id}"),
                "img_url": self._metadata_for_asin(self.id2item.get(item_id, "?")).get("img_url", ""),
            }
            for item_id in merged[-15:]
        ]

    def record_interaction(self, user_id: str, product_asin: str, action_type: str, rating: float | None = None) -> dict:
        """Lưu hành vi vào DB, cập nhật session và trả gợi ý mới ngay."""
        try:
            self._execute_write(
                "INSERT INTO interactions (user_id, product_id, action_type, rating) VALUES (%s, %s, %s, %s)",
                (str(user_id), product_asin, action_type, rating),
            )
        except Exception as exc:
            print(f"[ERROR] record_interaction DB: {exc}")

        item_id = self.item2id.get(product_asin, -1)
        if item_id > 0:
            if action_type in ("purchase", "like") or (rating and rating >= 4):
                session_store.boost_sequence(user_id, item_id, times=3)
            elif action_type == "cart":
                session_store.boost_sequence(user_id, item_id, times=2)
            else:
                session_store.add_to_sequence(user_id, item_id)

        return self.get_recommendations_for_user(user_id, top_k=12)

    def get_product_detail(self, asin: str) -> dict | None:
        """Lấy chi tiết sản phẩm theo ASIN từ MySQL hoặc metadata artifact."""
        item_id = self.item2id.get(asin, -1)
        metadata = self._metadata_for_asin(asin)
        if item_id <= 0 and not metadata:
            return None
        return self._enrich(item_id, 0.0)

    def delete_interaction(self, user_id: str, product_asin: str) -> dict:
        """Xóa sản phẩm khỏi lịch sử DB/session và trả lịch sử + gợi ý mới."""
        try:
            self._execute_write(
                "DELETE FROM interactions WHERE user_id = %s AND product_id = %s",
                (str(user_id), product_asin),
            )
        except Exception as exc:
            print(f"[ERROR] delete_interaction DB: {exc}")

        item_id = self.item2id.get(product_asin, -1)
        if item_id > 0:
            session_store.remove_from_sequence(user_id, item_id)

        recommendations = self.get_recommendations_for_user(user_id, top_k=12)
        return {
            "history": self.get_user_history(user_id) or [],
            "recommendations": recommendations.get("recommendations", []),
            "source": recommendations.get("source", "popular"),
        }

    def get_stats(self) -> dict:
        """Trả kết quả đánh giá model được lưu trong artifact."""
        return self.artifacts.get("results", {"HR_10": 0.198, "NDCG_10": 0.105})

    def invalidate_popular_cache(self) -> None:
        """Xóa cache popular sau khi có interaction mới."""
        self.popular_cache = []


recommender_service = RecommenderService()
