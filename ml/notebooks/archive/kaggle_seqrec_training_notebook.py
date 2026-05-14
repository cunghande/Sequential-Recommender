# %% [markdown]
# # Sequential Product Recommendation - Kaggle Training Notebook
#
# Use this notebook on Kaggle GPU to train and compare:
# - Popularity baseline
# - Item-KNN baseline
# - LSTMRec
# - GRU4Rec
#
# The output artifacts are compatible with the demo backend:
# - `exports/GRU4Rec_best.pt`
# - `exports/LSTM_best.pt`
# - `exports/model_artifacts.pkl`
# - `exports/metrics_summary.csv`
# - `exports/web_export.json`

# %%
import gzip
import json
import math
import os
import pickle
import random
import shutil
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.utils.rnn as rnn_utils
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from torch.utils.data import DataLoader, Dataset
from tqdm.auto import tqdm

sns.set_theme(style="darkgrid")

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", DEVICE)
print("PyTorch:", torch.__version__)

ROOT = Path(".")
OUTPUT_DIR = ROOT / "outputs"
CHECKPOINT_DIR = ROOT / "checkpoints"
EXPORT_DIR = ROOT / "exports"
for d in [OUTPUT_DIR, CHECKPOINT_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Set True for a 5-10 minute smoke test. Set False for the real report run.
RUN_FAST_SMOKE = False

# Kaggle tip:
# Add the Amazon Video Games dataset, then update these names if Kaggle uses
# another input folder name.
REVIEW_FILE_CANDIDATES = [
    "/kaggle/input/amazon-video-games-recommendation/Video_Games.jsonl/Video_Games.jsonl",
    "/kaggle/input/amazon-video-games/Video_Games.jsonl",
    "/kaggle/input/amazon-video-games-reviews/Video_Games.jsonl",
    "/kaggle/input/amazon-reviews-2023-video-games/Video_Games.jsonl",
    "Video_Games.jsonl",
    "/kaggle/input/amazon-video-games/Video_Games.jsonl.gz",
    "/kaggle/input/amazon-video-games-reviews/Video_Games.jsonl.gz",
    "/kaggle/input/amazon-reviews-2023-video-games/Video_Games.jsonl.gz",
    "Video_Games.jsonl.gz",
]
META_FILE_CANDIDATES = [
    "/kaggle/input/amazon-video-games-recommendation/meta_Video_Games.jsonl/meta_Video_Games.jsonl",
    "/kaggle/input/amazon-video-games/meta_Video_Games.jsonl",
    "/kaggle/input/amazon-video-games-reviews/meta_Video_Games.jsonl",
    "/kaggle/input/amazon-reviews-2023-video-games/meta_Video_Games.jsonl",
    "meta_Video_Games.jsonl",
    "/kaggle/input/amazon-video-games/meta_Video_Games.jsonl.gz",
    "/kaggle/input/amazon-video-games-reviews/meta_Video_Games.jsonl.gz",
    "/kaggle/input/amazon-reviews-2023-video-games/meta_Video_Games.jsonl.gz",
    "meta_Video_Games.jsonl.gz",
]


def find_file(candidates, suffix):
    for p in candidates:
        path = Path(p)
        if path.is_file():
            return path
        if path.is_dir():
            matches = [m for m in path.rglob(suffix) if m.is_file()]
            if matches:
                return matches[0]
    kaggle_root = Path("/kaggle/input")
    if kaggle_root.exists():
        matches = [m for m in kaggle_root.rglob(suffix) if m.is_file()]
        if matches:
            return matches[0]
    raise FileNotFoundError(f"Cannot find {suffix}. Update the candidate paths.")


REVIEW_FILE = find_file(REVIEW_FILE_CANDIDATES, "Video_Games.jsonl")
META_FILE = find_file(META_FILE_CANDIDATES, "meta_Video_Games.jsonl")
print("Review file:", REVIEW_FILE)
print("Meta file:", META_FILE)

# %% [markdown]
# ## 1. Data Collection

# %%
def resolve_readable_file(path):
    path = Path(path)
    if path.is_file():
        return path
    if path.is_dir():
        candidates = [
            m for pattern in [path.name, "*.jsonl", "*.jsonl.gz", "*.json", "*.json.gz"]
            for m in path.rglob(pattern)
            if m.is_file()
        ]
        if candidates:
            return candidates[0]
    raise FileNotFoundError(f"Cannot find a readable data file inside: {path}")


def open_text(path):
    path = resolve_readable_file(path)
    return gzip.open(path, "rt", encoding="utf-8") if str(path).endswith(".gz") else open(path, "rt", encoding="utf-8")


def normalize_timestamp(value):
    ts = int(value or 0)
    # Amazon 2023 often stores milliseconds. Old datasets often store seconds.
    return ts // 1000 if ts > 10_000_000_000 else ts


def load_reviews(path, limit=None):
    rows = []
    with open_text(path) as f:
        for i, line in enumerate(tqdm(f, desc="Reading reviews")):
            if limit and i >= limit:
                break
            try:
                r = json.loads(line)
                user_id = r.get("user_id") or r.get("reviewerID")
                item_id = r.get("parent_asin") or r.get("asin")
                rating = float(r.get("rating", r.get("overall", 0)))
                timestamp = normalize_timestamp(r.get("timestamp", r.get("unixReviewTime", 0)))
                if user_id and item_id and timestamp:
                    rows.append((user_id, item_id, rating, timestamp))
            except Exception:
                continue
    return pd.DataFrame(rows, columns=["user_id", "item_id", "rating", "timestamp"])


def load_metadata(path, limit=None):
    meta = {}
    with open_text(path) as f:
        for i, line in enumerate(tqdm(f, desc="Reading metadata")):
            if limit and i >= limit:
                break
            try:
                m = json.loads(line)
                asin = m.get("parent_asin") or m.get("asin")
                if not asin:
                    continue
                cats = m.get("categories", []) or m.get("category", [])
                category = cats[-1] if cats and isinstance(cats[-1], str) else "Unknown"
                price_raw = m.get("price", 0)
                try:
                    price = float(str(price_raw).replace("$", "").replace(",", ""))
                except Exception:
                    price = 0.0
                images = m.get("images") or []
                img_url = ""
                if images and isinstance(images[0], dict):
                    img_url = images[0].get("large") or images[0].get("hi_res") or images[0].get("thumb") or ""
                meta[asin] = {
                    "title": str(m.get("title", asin))[:180],
                    "category": str(category)[:80],
                    "price": price,
                    "avg_rating": float(m.get("average_rating", 0) or 0),
                    "img_url": img_url,
                }
            except Exception:
                continue
    return meta


limit = 300_000 if RUN_FAST_SMOKE else None
df_reviews = load_reviews(REVIEW_FILE, limit=limit).dropna()
meta = load_metadata(META_FILE)
df_reviews["category"] = df_reviews["item_id"].map(lambda x: meta.get(x, {}).get("category", "Unknown"))
df_reviews["title"] = df_reviews["item_id"].map(lambda x: meta.get(x, {}).get("title", x))

print(df_reviews.head())
print("Rows:", len(df_reviews), "Users:", df_reviews.user_id.nunique(), "Items:", df_reviews.item_id.nunique())

# %% [markdown]
# ## 2. EDA / Data Observation

# %%
def dataset_stats(df, name):
    n_users = df["user_id"].nunique()
    n_items = df["item_id"].nunique()
    n_inter = len(df)
    sparsity = 1 - (n_inter / max(n_users * n_items, 1))
    return {
        "dataset": name,
        "interactions": n_inter,
        "users": n_users,
        "items": n_items,
        "avg_rating": float(df["rating"].mean()),
        "sparsity": sparsity,
        "min_date": pd.to_datetime(df["timestamp"].min(), unit="s").date().isoformat(),
        "max_date": pd.to_datetime(df["timestamp"].max(), unit="s").date().isoformat(),
    }


raw_stats = dataset_stats(df_reviews, "raw")
display(pd.DataFrame([raw_stats]))

plt.figure(figsize=(7, 4))
rating_counts = df_reviews["rating"].value_counts().sort_index()
sns.barplot(x=rating_counts.index.astype(str), y=rating_counts.values, color="#2563eb")
plt.title("Rating Distribution")
plt.xlabel("Rating")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "01_rating_distribution.png", dpi=160)
plt.show()

seq_lens_raw = df_reviews.groupby("user_id").size()
plt.figure(figsize=(8, 4))
plt.hist(seq_lens_raw.clip(upper=60), bins=60, color="#16a34a", edgecolor="white", linewidth=0.2)
plt.axvline(5, color="red", linestyle="--", label="k=5")
plt.axvline(10, color="orange", linestyle="--", label="k=10")
plt.title("Sequence Length Distribution")
plt.xlabel("Interactions per user")
plt.ylabel("Users")
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "02_sequence_length.png", dpi=160)
plt.show()

top_cats = df_reviews["category"].value_counts().head(15)
plt.figure(figsize=(9, 5))
sns.barplot(x=top_cats.values, y=top_cats.index, color="#0f766e")
plt.title("Top Categories")
plt.xlabel("Interactions")
plt.ylabel("Category")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "03_top_categories.png", dpi=160)
plt.show()

top_items_eda = (
    df_reviews.groupby("item_id")
    .agg(count=("user_id", "count"), avg_rating=("rating", "mean"), title=("title", "first"), category=("category", "first"))
    .sort_values("count", ascending=False)
    .head(20)
)
display(top_items_eda)
top_items_eda.to_csv(OUTPUT_DIR / "top_items.csv")

# %% [markdown]
# ## 3. Preprocessing Experiments

# %%
@dataclass
class ExperimentConfig:
    name: str
    min_rating: float | None = None
    k_core: int = 5
    max_len: int = 50
    num_neg: int = 99
    emb_dim: int = 64
    hidden: int = 128
    n_layers: int = 1
    dropout: float = 0.2
    epochs: int = 30
    patience: int = 5
    lr: float = 1e-3
    weight_decay: float = 1e-5
    batch_size: int = 512
    train_lstm: bool = True
    train_gru: bool = True


def k_core_filter(df, k=5):
    work = df.copy()
    rounds = 0
    while True:
        before = len(work)
        item_counts = work["item_id"].value_counts()
        work = work[work["item_id"].isin(item_counts[item_counts >= k].index)]
        user_counts = work["user_id"].value_counts()
        work = work[work["user_id"].isin(user_counts[user_counts >= k].index)]
        rounds += 1
        if len(work) == before:
            break
    return work.reset_index(drop=True), rounds


def build_processed(df_source, cfg: ExperimentConfig):
    df = df_source.copy()
    if cfg.min_rating is not None:
        df = df[df["rating"] >= cfg.min_rating].copy()
    before_stats = dataset_stats(df, f"{cfg.name}_before_kcore")
    df, rounds = k_core_filter(df, cfg.k_core)
    after_stats = dataset_stats(df, cfg.name)
    after_stats["k_core_rounds"] = rounds
    after_stats["min_rating"] = cfg.min_rating if cfg.min_rating is not None else "all"

    users = sorted(df["user_id"].unique())
    items = sorted(df["item_id"].unique())
    user2id = {u: i + 1 for i, u in enumerate(users)}
    item2id = {it: i + 1 for i, it in enumerate(items)}
    id2user = {v: k for k, v in user2id.items()}
    id2item = {v: k for k, v in item2id.items()}

    df["user"] = df["user_id"].map(user2id)
    df["item"] = df["item_id"].map(item2id)
    df = df.sort_values(["user", "timestamp"])
    sequences = df.groupby("user")["item"].apply(list).to_dict()

    train_data, val_data, test_data = {}, {}, {}
    for user, seq in sequences.items():
        if len(seq) < 3:
            continue
        train_data[user] = seq[:-2]
        val_data[user] = seq[-2]
        test_data[user] = seq[-1]

    popular_items = [int(i) for i, _ in Counter(df["item"]).most_common()]
    return {
        "df": df,
        "before_stats": before_stats,
        "after_stats": after_stats,
        "user2id": user2id,
        "item2id": item2id,
        "id2user": id2user,
        "id2item": id2item,
        "train": train_data,
        "val": val_data,
        "test": test_data,
        "popular_items": popular_items,
        "num_users": len(users),
        "num_items": len(items),
    }


class TrainDataset(Dataset):
    def __init__(self, train_data, max_len):
        self.max_len = max_len
        self.samples = []
        for _, seq in train_data.items():
            for i in range(1, len(seq)):
                self.samples.append((seq[:i], seq[i]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        inp, tgt = self.samples[idx]
        inp = inp[-self.max_len:]
        seq_len = len(inp)
        padded = [0] * (self.max_len - seq_len) + inp
        return {
            "item_seq": torch.tensor(padded, dtype=torch.long),
            "seq_len": torch.tensor(seq_len, dtype=torch.long),
            "target": torch.tensor(tgt, dtype=torch.long),
        }


class EvalDataset(Dataset):
    def __init__(self, history, eval_data, all_history, num_items, max_len, num_neg, seed=42):
        self.samples = []
        rng = random.Random(seed)
        all_items = list(range(1, num_items + 1))
        for user, pos in tqdm(eval_data.items(), desc="Building eval candidates"):
            if user not in history:
                continue
            seq = history[user]
            known = set(all_history.get(user, [])) | {pos}
            available = num_items - len(known)
            if available <= 0:
                continue
            negs = set()
            while len(negs) < min(num_neg, available):
                n = rng.choice(all_items)
                if n not in known:
                    negs.add(n)
            inp = seq[-max_len:]
            seq_len = len(inp)
            padded = [0] * (max_len - seq_len) + inp
            self.samples.append({
                "item_seq": torch.tensor(padded, dtype=torch.long),
                "seq_len": torch.tensor(seq_len, dtype=torch.long),
                "candidates": torch.tensor([pos] + sorted(negs), dtype=torch.long),
                "user": user,
            })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]

# %% [markdown]
# ## 4. Models and Metrics

# %%
K_LIST = [5, 10, 20]


def compute_metrics(scores, k_list=K_LIST):
    # Positive item is always candidate index 0.
    order = torch.argsort(scores, dim=1, descending=True)
    pos_rank = (order == 0).nonzero(as_tuple=False)[:, 1] + 1
    result = {}
    for k in k_list:
        hit = (pos_rank <= k).float()
        ndcg = torch.where(pos_rank <= k, 1.0 / torch.log2(pos_rank.float() + 1), torch.zeros_like(pos_rank, dtype=torch.float))
        result[f"HR@{k}"] = hit.mean().item()
        result[f"NDCG@{k}"] = ndcg.mean().item()
    return result


@torch.no_grad()
def evaluate_model(model, loader, device, model_type="neural"):
    if model_type == "neural":
        model.eval()
    acc = {f"HR@{k}": [] for k in K_LIST}
    acc.update({f"NDCG@{k}": [] for k in K_LIST})
    for batch in tqdm(loader, desc=f"Evaluating {model_type}", leave=False):
        cands = batch["candidates"]
        seq = batch["item_seq"]
        seq_len = batch["seq_len"]
        if model_type in {"popularity", "itemknn"}:
            scores = model.predict_scores_batch(seq, seq_len, cands)
        else:
            scores = model.predict(seq.to(device), seq_len.to(device), cands.to(device)).cpu()
        metrics = compute_metrics(scores)
        for key, value in metrics.items():
            acc[key].append(value)
    return {k: float(np.mean(v)) for k, v in acc.items()}


class PopularityBaseline:
    def __init__(self, popular_items):
        self.rank = {item: idx for idx, item in enumerate(popular_items)}
        self.default_rank = len(popular_items) + 1

    def predict_scores_batch(self, seq, seq_len, candidates):
        cands = candidates.numpy()
        scores = np.zeros(cands.shape, dtype=np.float32)
        for b in range(cands.shape[0]):
            for j, item in enumerate(cands[b]):
                scores[b, j] = -self.rank.get(int(item), self.default_rank)
        return torch.tensor(scores, dtype=torch.float32)


class ItemKNN:
    def __init__(self, train_data, num_users, num_items, top_k_sim=50, window=5):
        self.window = window
        rows, cols = [], []
        for user, seq in train_data.items():
            for item in set(seq):
                rows.append(item - 1)
                cols.append(user - 1)
        data = np.ones(len(rows), dtype=np.float32)
        item_user = csr_matrix((data, (rows, cols)), shape=(num_items, num_users))
        n_neighbors = min(top_k_sim + 1, num_items)
        nn_model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=n_neighbors)
        nn_model.fit(item_user)
        distances, indices = nn_model.kneighbors(item_user, return_distance=True)
        self.neighbors = {}
        for item_idx in range(num_items):
            pairs = []
            for dist, nei_idx in zip(distances[item_idx], indices[item_idx]):
                if nei_idx == item_idx:
                    continue
                sim = 1.0 - float(dist)
                if sim > 0:
                    pairs.append((int(nei_idx + 1), sim))
            self.neighbors[item_idx + 1] = pairs[:top_k_sim]

    def score_one(self, history, candidates):
        window_items = history[-self.window:]
        cand_pos = {int(c): i for i, c in enumerate(candidates)}
        scores = np.zeros(len(candidates), dtype=np.float32)
        for ref in window_items:
            for nei, sim in self.neighbors.get(int(ref), []):
                pos = cand_pos.get(nei)
                if pos is not None:
                    scores[pos] += sim
        return scores / max(len(window_items), 1)

    def predict_scores_batch(self, seq, seq_len, candidates):
        cands = candidates.numpy()
        scores = np.zeros(cands.shape, dtype=np.float32)
        for b in range(cands.shape[0]):
            hist = [int(x) for x in seq[b, -int(seq_len[b]):].tolist() if int(x) > 0]
            scores[b] = self.score_one(hist, cands[b])
        return torch.tensor(scores, dtype=torch.float32)


class LSTMRec(nn.Module):
    def __init__(self, num_items, emb_dim=64, hidden=128, n_layers=1, dropout=0.2):
        super().__init__()
        self.hidden = hidden
        self.embedding = nn.Embedding(num_items + 1, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(emb_dim, hidden, n_layers, batch_first=True, dropout=dropout if n_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, emb_dim)
        nn.init.xavier_normal_(self.embedding.weight)
        nn.init.xavier_normal_(self.fc.weight)

    def forward(self, item_seq, seq_len):
        emb = self.dropout(self.embedding(item_seq))
        packed = rnn_utils.pack_padded_sequence(emb, seq_len.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(packed)
        out, _ = rnn_utils.pad_packed_sequence(out, batch_first=True)
        idx = (seq_len - 1).long().unsqueeze(1).unsqueeze(2).expand(-1, 1, self.hidden).to(out.device)
        last = out.gather(1, idx).squeeze(1)
        return self.fc(self.dropout(last))

    def predict(self, item_seq, seq_len, candidates):
        out = self.forward(item_seq, seq_len)
        embs = self.embedding(candidates)
        return torch.bmm(embs, out.unsqueeze(-1)).squeeze(-1)


class GRU4Rec(nn.Module):
    def __init__(self, num_items, emb_dim=64, hidden=128, n_layers=1, dropout=0.2):
        super().__init__()
        self.hidden = hidden
        self.embedding = nn.Embedding(num_items + 1, emb_dim, padding_idx=0)
        self.gru = nn.GRU(emb_dim, hidden, n_layers, batch_first=True, dropout=dropout if n_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, emb_dim)
        nn.init.xavier_normal_(self.embedding.weight)
        nn.init.xavier_normal_(self.fc.weight)

    def forward(self, item_seq, seq_len):
        emb = self.dropout(self.embedding(item_seq))
        packed = rnn_utils.pack_padded_sequence(emb, seq_len.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.gru(packed)
        out, _ = rnn_utils.pad_packed_sequence(out, batch_first=True)
        idx = (seq_len - 1).long().unsqueeze(1).unsqueeze(2).expand(-1, 1, self.hidden).to(out.device)
        last = out.gather(1, idx).squeeze(1)
        return self.fc(self.dropout(last))

    def predict(self, item_seq, seq_len, candidates):
        out = self.forward(item_seq, seq_len)
        embs = self.embedding(candidates)
        return torch.bmm(embs, out.unsqueeze(-1)).squeeze(-1)

# %% [markdown]
# ## 5. Training and Hyperparameter Tuning

# %%
def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    losses = []
    for batch in tqdm(loader, desc="Training", leave=False):
        item_seq = batch["item_seq"].to(device)
        seq_len = batch["seq_len"].to(device)
        target = batch["target"].to(device)
        optimizer.zero_grad()
        out = model(item_seq, seq_len)
        logits = out @ model.embedding.weight[1:].T
        loss = criterion(logits, target - 1)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(loss.item())
    return float(np.mean(losses))


def train_full(model, model_name, train_loader, val_loader, test_loader, cfg: ExperimentConfig, num_items):
    model = model.to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    criterion = nn.CrossEntropyLoss()
    best_ndcg = -1.0
    best_path = CHECKPOINT_DIR / f"{cfg.name}_{model_name}_best.pt"
    no_improve = 0
    history = []

    for epoch in range(1, cfg.epochs + 1):
        loss = train_one_epoch(model, train_loader, optimizer, criterion, DEVICE)
        scheduler.step()
        val_metrics = evaluate_model(model, val_loader, DEVICE, model_type="neural")
        row = {"experiment": cfg.name, "model": model_name, "epoch": epoch, "loss": loss, **{f"val_{k}": v for k, v in val_metrics.items()}}
        history.append(row)
        print(f"[{cfg.name}][{model_name}] ep={epoch:02d} loss={loss:.4f} val_HR@10={val_metrics['HR@10']:.4f} val_NDCG@10={val_metrics['NDCG@10']:.4f}")
        if val_metrics["NDCG@10"] > best_ndcg:
            best_ndcg = val_metrics["NDCG@10"]
            torch.save(model.state_dict(), best_path)
            no_improve = 0
            print("  saved best:", best_path)
        else:
            no_improve += 1
            if no_improve >= cfg.patience:
                print("  early stopping")
                break

    model.load_state_dict(torch.load(best_path, map_location=DEVICE, weights_only=True))
    test_metrics = evaluate_model(model, test_loader, DEVICE, model_type="neural")
    return model, str(best_path), pd.DataFrame(history), test_metrics


def make_loaders(processed, cfg: ExperimentConfig):
    train_data = processed["train"]
    val_data = processed["val"]
    test_data = processed["test"]
    train_ds = TrainDataset(train_data, cfg.max_len)
    all_hist_val = {u: list(seq) + [val_data[u], test_data[u]] for u, seq in train_data.items() if u in val_data and u in test_data}
    val_ds = EvalDataset(train_data, val_data, all_hist_val, processed["num_items"], cfg.max_len, cfg.num_neg, seed=SEED)
    train4test = {u: seq + [val_data[u]] for u, seq in train_data.items() if u in val_data}
    all_hist_test = all_hist_val
    test_ds = EvalDataset(train4test, test_data, all_hist_test, processed["num_items"], cfg.max_len, cfg.num_neg, seed=SEED + 1)
    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=2, pin_memory=torch.cuda.is_available())
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, shuffle=False, num_workers=2, pin_memory=torch.cuda.is_available())
    test_loader = DataLoader(test_ds, batch_size=cfg.batch_size, shuffle=False, num_workers=2, pin_memory=torch.cuda.is_available())
    return train_loader, val_loader, test_loader


def run_experiment(name, df_source, cfg: ExperimentConfig):
    print("=" * 80)
    print("Experiment:", name)
    print(cfg)
    started = time.time()
    processed = build_processed(df_source, cfg)
    train_loader, val_loader, test_loader = make_loaders(processed, cfg)
    rows = []
    histories = []
    checkpoints = {}

    popularity = PopularityBaseline(processed["popular_items"])
    pop_metrics = evaluate_model(popularity, test_loader, DEVICE, model_type="popularity")
    rows.append({"experiment": cfg.name, "model": "Popularity", **pop_metrics})

    itemknn = ItemKNN(processed["train"], processed["num_users"], processed["num_items"], top_k_sim=50, window=5)
    knn_metrics = evaluate_model(itemknn, test_loader, DEVICE, model_type="itemknn")
    rows.append({"experiment": cfg.name, "model": "Item-KNN", **knn_metrics})

    if cfg.train_lstm:
        lstm = LSTMRec(processed["num_items"], cfg.emb_dim, cfg.hidden, cfg.n_layers, cfg.dropout)
        lstm, path, hist, metrics = train_full(lstm, "LSTM", train_loader, val_loader, test_loader, cfg, processed["num_items"])
        rows.append({"experiment": cfg.name, "model": "LSTM", **metrics})
        histories.append(hist)
        checkpoints["LSTM"] = path

    if cfg.train_gru:
        gru = GRU4Rec(processed["num_items"], cfg.emb_dim, cfg.hidden, cfg.n_layers, cfg.dropout)
        gru, path, hist, metrics = train_full(gru, "GRU4Rec", train_loader, val_loader, test_loader, cfg, processed["num_items"])
        rows.append({"experiment": cfg.name, "model": "GRU4Rec", **metrics})
        histories.append(hist)
        checkpoints["GRU4Rec"] = path

    metrics_df = pd.DataFrame(rows)
    history_df = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    processed["elapsed_minutes"] = round((time.time() - started) / 60, 2)
    return {
        "config": cfg,
        "processed": processed,
        "metrics": metrics_df,
        "history": history_df,
        "checkpoints": checkpoints,
    }

# %% [markdown]
# ## 6. Run Experiments

# %%
if RUN_FAST_SMOKE:
    experiment_configs = [
        ExperimentConfig(name="smoke_positive_k5_small", min_rating=4, k_core=5, max_len=50, emb_dim=32, hidden=64, epochs=2, patience=1, batch_size=256),
    ]
else:
    experiment_configs = [
        ExperimentConfig(name="all_ratings_k5_small", min_rating=None, k_core=5, max_len=50, emb_dim=64, hidden=128, epochs=12, patience=3, train_lstm=True, train_gru=True),
        ExperimentConfig(name="positive_k5_small", min_rating=4, k_core=5, max_len=50, emb_dim=64, hidden=128, epochs=12, patience=3, train_lstm=True, train_gru=True),
        ExperimentConfig(name="positive_k10_gru_tuned", min_rating=4, k_core=10, max_len=100, emb_dim=128, hidden=256, epochs=20, patience=5, train_lstm=False, train_gru=True),
    ]

all_runs = []
for cfg in experiment_configs:
    run = run_experiment(cfg.name, df_reviews, cfg)
    all_runs.append(run)

metrics_summary = pd.concat([r["metrics"] for r in all_runs], ignore_index=True)
history_summary = pd.concat([r["history"] for r in all_runs if len(r["history"])], ignore_index=True)
stats_summary = pd.DataFrame([r["processed"]["after_stats"] for r in all_runs])

display(metrics_summary)
display(stats_summary)

metrics_summary.to_csv(EXPORT_DIR / "metrics_summary.csv", index=False)
history_summary.to_csv(EXPORT_DIR / "training_history.csv", index=False)
stats_summary.to_csv(EXPORT_DIR / "preprocessing_stats.csv", index=False)

# %% [markdown]
# ## 7. Evaluation Charts

# %%
plt.figure(figsize=(10, 5))
plot_df = metrics_summary[metrics_summary["model"].isin(["Popularity", "Item-KNN", "LSTM", "GRU4Rec"])]
sns.barplot(data=plot_df, x="experiment", y="HR@10", hue="model")
plt.xticks(rotation=25, ha="right")
plt.title("HR@10 Model Comparison")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "04_hr10_model_comparison.png", dpi=160)
plt.show()

plt.figure(figsize=(10, 5))
sns.barplot(data=plot_df, x="experiment", y="NDCG@10", hue="model")
plt.xticks(rotation=25, ha="right")
plt.title("NDCG@10 Model Comparison")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "05_ndcg10_model_comparison.png", dpi=160)
plt.show()

if len(history_summary):
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=history_summary, x="epoch", y="val_NDCG@10", hue="experiment", style="model", markers=True)
    plt.title("Validation NDCG@10 by Epoch")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "06_val_ndcg10_by_epoch.png", dpi=160)
    plt.show()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=history_summary, x="epoch", y="loss", hue="experiment", style="model", markers=True)
    plt.title("Training Loss by Epoch")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "07_training_loss.png", dpi=160)
    plt.show()

# %% [markdown]
# ## 8. Export for Demo

# %%
def pick_best_demo_run(all_runs):
    candidates = []
    for run in all_runs:
        metrics = run["metrics"]
        for _, row in metrics.iterrows():
            if row["model"] in {"GRU4Rec", "LSTM"}:
                candidates.append((row["model"], row["NDCG@10"], row["HR@10"], run))
    if not candidates:
        raise RuntimeError("No neural model was trained.")
    candidates = sorted(candidates, key=lambda x: (x[1], x[2]), reverse=True)
    best_model, best_ndcg, best_hr, best_run = candidates[0]

    # Prefer GRU4Rec if it is close to the best model because the demo backend already uses GRU4Rec.
    gru_candidates = [c for c in candidates if c[0] == "GRU4Rec"]
    if gru_candidates and (best_ndcg - gru_candidates[0][1] <= 0.01):
        return "GRU4Rec", gru_candidates[0][3]
    return best_model, best_run


best_model_name, best_run = pick_best_demo_run(all_runs)
best_processed = best_run["processed"]
best_cfg = best_run["config"]
best_ckpt = best_run["checkpoints"][best_model_name]
print("Best demo model:", best_model_name, best_ckpt)

if best_model_name == "GRU4Rec":
    shutil.copy(best_ckpt, EXPORT_DIR / "GRU4Rec_best.pt")
else:
    # Keep backend compatibility: export best GRU if available, plus selected LSTM separately.
    if "GRU4Rec" in best_run["checkpoints"]:
        shutil.copy(best_run["checkpoints"]["GRU4Rec"], EXPORT_DIR / "GRU4Rec_best.pt")
    shutil.copy(best_ckpt, EXPORT_DIR / "LSTM_best.pt")

for run in all_runs:
    if "LSTM" in run["checkpoints"]:
        shutil.copy(run["checkpoints"]["LSTM"], EXPORT_DIR / "LSTM_best.pt")
    if "GRU4Rec" in run["checkpoints"]:
        # Keep the strongest GRU under the backend-compatible name.
        run_metric = run["metrics"].query("model == 'GRU4Rec'")
        if len(run_metric) and run is best_run:
            shutil.copy(run["checkpoints"]["GRU4Rec"], EXPORT_DIR / "GRU4Rec_best.pt")

config = {
    "num_items": best_processed["num_items"],
    "num_users": best_processed["num_users"],
    "emb_dim": best_cfg.emb_dim,
    "hidden": best_cfg.hidden,
    "n_layers": best_cfg.n_layers,
    "dropout": best_cfg.dropout,
    "max_len": best_cfg.max_len,
    "k_core": best_cfg.k_core,
    "num_neg": best_cfg.num_neg,
    "min_rating": best_cfg.min_rating,
    "selected_model": best_model_name,
}

artifact_meta = {asin: meta.get(asin, {}) for asin in best_processed["item2id"].keys()}
model_artifacts = {
    "config": config,
    "results": {
        "metrics_summary": metrics_summary.to_dict("records"),
        "preprocessing_stats": stats_summary.to_dict("records"),
    },
    "mappings": {
        "user2id": best_processed["user2id"],
        "item2id": best_processed["item2id"],
        "id2item": best_processed["id2item"],
        "meta": artifact_meta,
    },
    "sequences": {
        "train": best_processed["train"],
        "val": best_processed["val"],
        "test": best_processed["test"],
    },
    "popular_items": best_processed["popular_items"][:1000],
}

with open(EXPORT_DIR / "model_artifacts.pkl", "wb") as f:
    pickle.dump(model_artifacts, f)

web_products = []
for item_id in best_processed["popular_items"][:5000]:
    asin = best_processed["id2item"].get(item_id)
    info = meta.get(asin, {})
    web_products.append({
        "item_id": int(item_id),
        "asin": asin,
        "title": info.get("title", asin),
        "category": info.get("category", "Unknown"),
        "price": float(info.get("price", 0) or 0),
        "rating": float(info.get("avg_rating", 0) or 0),
        "img_url": info.get("img_url", ""),
    })

with open(EXPORT_DIR / "web_export.json", "w", encoding="utf-8") as f:
    json.dump({"products": web_products, "metrics": metrics_summary.to_dict("records"), "config": config}, f, ensure_ascii=False)

shutil.make_archive("seqrec_kaggle_exports", "zip", EXPORT_DIR)
print("Exported files:")
for p in sorted(EXPORT_DIR.iterdir()):
    print(" -", p)
print("Zip:", Path("seqrec_kaggle_exports.zip").resolve())

# %% [markdown]
# ## 9. Report Notes
#
# Put these points in the report:
# - Data was split chronologically with Leave-One-Out.
# - Metrics were computed with one positive item and 99 sampled negative items.
# - Popularity and Item-KNN are baselines.
# - LSTM and GRU4Rec are sequential neural recommenders.
# - Best checkpoint is selected by validation NDCG@10, then evaluated on the test set.
# - The demo uses the exported GRU4Rec checkpoint and the same item/user mappings.
