from collections import Counter
from pathlib import Path
from typing import Any
import json
import re
from urllib import error as url_error
from urllib import request as url_request

import pickle
import torch

from backend.app.core.config import settings
from backend.models.gru4rec import GRU4Rec
from backend.services import session as session_store
from backend.services.db import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_DIRS = [
    PROJECT_ROOT / "ml" / "checkpoints",
    PROJECT_ROOT / "checkpoints",
]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TITLE_STOPWORDS = {
    "and",
    "for",
    "the",
    "with",
    "edition",
    "digital",
    "code",
    "game",
    "games",
    "playstation",
    "xbox",
    "nintendo",
    "switch",
}


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

    def _ensure_interaction_user(self, user_id: str) -> None:
        """Tạo user guest tối giản để interaction không vi phạm khóa ngoại."""
        if not str(user_id).startswith("guest_"):
            return
        self._execute_write(
            """
            INSERT IGNORE INTO users (user_id, email, full_name, password_hash)
            VALUES (%s, %s, %s, NULL)
            """,
            (str(user_id), f"{user_id}@guest.local", "Guest User"),
        )

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

    def _title_tokens(self, title: str) -> set[str]:
        tokens = re.findall(r"[a-z0-9]+", (title or "").lower())
        return {token for token in tokens if len(token) > 2 and token not in TITLE_STOPWORDS}

    def _popular_item_scores(self, limit: int = 500) -> dict[int, float]:
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
                (limit,),
            )
        except Exception as exc:
            print(f"[ERROR] _popular_item_scores: {exc}")
            return {}

        raw_scores: dict[int, float] = {}
        for row in rows:
            item_id = self.item2id.get(row["product_id"], -1)
            if item_id > 0:
                raw_scores[item_id] = float(row["popularity_score"] or 0.0)

        max_score = max(raw_scores.values(), default=0.0)
        if max_score <= 0:
            return {}
        return {item_id: score / max_score for item_id, score in raw_scores.items()}

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

    # Colab is optional and stateless: it only receives a sequence and returns item_id + score.
    # Product metadata, user history, DB writes, and fallback behavior stay in the local backend.
    def _colab_endpoint(self) -> str:
        base_url = settings.colab_model_api_url.rstrip("/")
        if not base_url:
            return ""
        if base_url.endswith("/recommend/sequence"):
            return base_url
        return f"{base_url}/recommend/sequence"

    def _predict_with_colab(self, history: list[int], top_k: int) -> list[dict]:
        if not settings.use_colab_model:
            return []

        endpoint = self._colab_endpoint()
        if not endpoint:
            return []

        history = [item_id for item_id in history if item_id > 0]
        if not history:
            return []

        payload = json.dumps({"sequence": history, "top_k": top_k}).encode("utf-8")
        request = url_request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with url_request.urlopen(request, timeout=settings.colab_model_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, ValueError, url_error.URLError, url_error.HTTPError) as exc:
            print(f"[WARNING] Colab model unavailable, using local recommender: {exc}")
            return []

        recommendations = data.get("recommendations", [])
        result: list[dict] = []
        seen = set(history)
        for item in recommendations:
            try:
                item_id = int(item.get("item_id"))
                score = float(item.get("score", 0.0))
            except (TypeError, ValueError):
                continue
            if item_id <= 0 or item_id in seen:
                continue
            result.append(self._enrich(item_id, score))
            if len(result) >= top_k:
                break
        return result

    def _fill_recommendations(self, primary: list[dict], fallback: list[dict], top_k: int) -> list[dict]:
        result: list[dict] = []
        seen: set[str] = set()
        for item in primary + fallback:
            asin = item.get("asin")
            if not asin or asin in seen:
                continue
            seen.add(asin)
            result.append(item)
            if len(result) >= top_k:
                break
        return result

    # Content ranking keeps recommendations aligned with the products the user actually viewed.
    # This prevents the neural model from dominating with generic high-score products.
    def _content_recommendations(self, history: list[int], top_k: int) -> list[dict]:
        history = [item_id for item_id in history if item_id > 0]
        if not history:
            return []

        seen = set(history)
        recent = history[-10:]
        category_weights: Counter[str] = Counter()
        token_weights: Counter[str] = Counter()

        for index, item_id in enumerate(reversed(recent), start=1):
            asin = self.id2item.get(item_id, "?")
            metadata = self._metadata_for_asin(asin)
            weight = max(0.3, 1.2 * (0.85 ** (index - 1)))
            category = metadata.get("category")
            if category:
                category_weights[str(category)] += weight
            for token in self._title_tokens(metadata.get("title", "")):
                token_weights[token] += weight

        popular_scores = self._popular_item_scores()
        candidates: list[tuple[float, int]] = []
        for asin, metadata in self.rich_metadata.items():
            item_id = self.item2id.get(asin, -1)
            if item_id <= 0 or item_id in seen:
                continue

            category = str(metadata.get("category") or "")
            title_tokens = self._title_tokens(metadata.get("title", ""))
            category_score = category_weights.get(category, 0.0) * 4.0
            token_score = sum(token_weights[token] for token in title_tokens) * 2.25
            popularity_score = popular_scores.get(item_id, 0.0) * 0.75
            score = category_score + token_score + popularity_score
            if score > 0:
                candidates.append((score, item_id))

        candidates.sort(key=lambda item: item[0], reverse=True)
        return [self._enrich(item_id, score) for score, item_id in candidates[:top_k]]

    # Final personalized ranking blends product similarity with model scores.
    # Recent items matter more, but repeated older categories can outweigh one newer outlier.
    def _history_context_items(self, history: list[int], limit: int = 3) -> list[dict]:
        context: list[dict] = []
        seen: set[int] = set()
        for item_id in reversed([item_id for item_id in history if item_id > 0]):
            if item_id in seen:
                continue
            seen.add(item_id)
            context.append(self._enrich(item_id))
            if len(context) >= limit:
                break
        return context

    def _hybrid_recommendations(
        self,
        history: list[int],
        top_k: int,
        model_items: list[dict] | None = None,
    ) -> list[dict]:
        content_items = self._content_recommendations(history, top_k * 3)
        model_items = model_items or self._predict(history, top_k * 3)

        combined: dict[str, dict] = {}
        history_len = len([item_id for item_id in history if item_id > 0])
        content_weight = 0.82 if history_len < 5 else 0.68
        model_weight = 1.0 - content_weight

        def add_items(items: list[dict], weight: float) -> None:
            if not items:
                return
            max_score = max((float(item.get("score") or 0.0) for item in items), default=0.0) or 1.0
            for rank, item in enumerate(items):
                asin = item.get("asin")
                if not asin:
                    continue
                normalized = float(item.get("score") or 0.0) / max_score
                rank_bonus = 1.0 / (rank + 1)
                score = weight * (normalized + rank_bonus)
                current = combined.get(asin)
                if current:
                    current["score"] += score
                else:
                    next_item = dict(item)
                    next_item["score"] = score
                    combined[asin] = next_item

        add_items(content_items, content_weight)
        add_items(model_items, model_weight)

        ranked = sorted(combined.values(), key=lambda item: item["score"], reverse=True)
        return [
            {**item, "score": round(float(item["score"]), 4)}
            for item in ranked[:top_k]
        ]

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
        if len(self.popular_cache) >= top_k:
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
        colab_recommendations = self._predict_with_colab(sequence, top_k)
        if colab_recommendations:
            hybrid_recommendations = self._hybrid_recommendations(
                sequence,
                top_k,
                colab_recommendations,
            )
            return {
                "source": "personalized",
                "model_source": "colab_hybrid",
                "context_items": self._history_context_items(sequence),
                "recommendations": hybrid_recommendations,
            }
        local_recommendations = self._hybrid_recommendations(sequence, top_k)
        return {
            "source": "personalized",
            "model_source": "local",
            "context_items": self._history_context_items(sequence),
            "recommendations": local_recommendations,
        }

    def get_recommendations(self, sequence_history: list[int], top_k: int = 10) -> list[dict]:
        """Gợi ý realtime từ sequence truyền trực tiếp, dùng cho endpoint demo."""
        colab_recommendations = self._predict_with_colab(sequence_history, top_k)
        if colab_recommendations:
            return self._hybrid_recommendations(sequence_history, top_k, colab_recommendations)
        local_recommendations = self._hybrid_recommendations(sequence_history, top_k)
        return local_recommendations

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
            self._ensure_interaction_user(str(user_id))
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
