"""
Colab-only model server for GRU4Rec inference.

Usage in Colab:
1. Upload/copy this file plus:
   - ml/checkpoints/GRU4Rec_best.pt
   - ml/checkpoints/model_artifacts.pkl
2. Install dependencies:
   !pip install fastapi uvicorn pyngrok nest_asyncio torch
3. Run:
   !python colab_model_api.py
4. Copy the printed Ngrok URL into backend/.env as COLAB_MODEL_API_URL.
"""

from pathlib import Path
from typing import Optional
import os
import pickle

import torch
import torch.nn as nn
import torch.nn.utils.rnn as rnn_utils
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CHECKPOINT_DIR = Path(os.getenv("CHECKPOINT_DIR", "ml/checkpoints"))


class GRU4Rec(nn.Module):
    def __init__(self, num_items, emb_dim=64, hidden=128, n_layers=1, dropout=0.2):
        super().__init__()
        self.hidden = hidden
        self.embedding = nn.Embedding(num_items + 1, emb_dim, padding_idx=0)
        self.gru = nn.GRU(emb_dim, hidden, n_layers, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden, emb_dim)

    def forward(self, item_seq, seq_len):
        emb = self.dropout(self.embedding(item_seq))
        packed = rnn_utils.pack_padded_sequence(
            emb,
            seq_len.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        out, _ = self.gru(packed)
        out, _ = rnn_utils.pad_packed_sequence(out, batch_first=True)
        idx = (seq_len - 1).long().unsqueeze(1).unsqueeze(2).expand(-1, 1, self.hidden)
        last = out.gather(1, idx.to(out.device)).squeeze(1)
        return self.fc(self.dropout(last))

    def predict_topk(self, item_seq, seq_len, top_k=10, exclude_ids=None):
        with torch.no_grad():
            out = self.forward(item_seq, seq_len)
            all_e = self.embedding.weight[1:]
            scores = (out @ all_e.T).squeeze(0)
            if exclude_ids:
                for item_id in exclude_ids:
                    if 1 <= item_id <= scores.size(0):
                        scores[item_id - 1] = -1e9
            top_scores, top_indices = torch.topk(scores, top_k)
            return (top_indices + 1).tolist(), top_scores.tolist()


class SequenceRecommendRequest(BaseModel):
    sequence: list[int]
    top_k: Optional[int] = 16


def load_model():
    artifact_path = CHECKPOINT_DIR / "model_artifacts.pkl"
    model_path = CHECKPOINT_DIR / "GRU4Rec_best.pt"
    if not artifact_path.exists():
        raise FileNotFoundError(f"Missing artifact: {artifact_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Missing model checkpoint: {model_path}")

    with artifact_path.open("rb") as file:
        artifacts = pickle.load(file)

    cfg = artifacts.get("config", {})
    model = GRU4Rec(
        cfg.get("num_items", 1000),
        cfg.get("emb_dim", 64),
        cfg.get("hidden", 128),
        cfg.get("n_layers", 1),
        cfg.get("dropout", 0.2),
    ).to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE, weights_only=True))
    model.eval()
    return model, cfg


app = FastAPI(title="SeqRec Colab Model API")
model, cfg = load_model()


@app.get("/health")
def health():
    return {
        "ok": True,
        "device": str(DEVICE),
        "num_items": cfg.get("num_items"),
    }


@app.post("/recommend/sequence")
def recommend_sequence(req: SequenceRecommendRequest):
    history = [item_id for item_id in req.sequence if item_id > 0]
    if not history:
        raise HTTPException(status_code=400, detail="sequence must contain at least one item_id")

    top_k = max(1, min(int(req.top_k or 16), 100))
    max_len = cfg.get("max_len", 50)
    history = history[-max_len:]
    padded = [0] * (max_len - len(history)) + history
    item_seq = torch.tensor([padded], dtype=torch.long).to(DEVICE)
    seq_len = torch.tensor([len(history)], dtype=torch.long).to(DEVICE)
    item_ids, scores = model.predict_topk(item_seq, seq_len, top_k=top_k, exclude_ids=history)
    return {
        "recommendations": [
            {"item_id": int(item_id), "score": round(float(score), 4)}
            for item_id, score in zip(item_ids, scores)
        ]
    }


if __name__ == "__main__":
    import nest_asyncio
    import uvicorn
    from pyngrok import ngrok

    nest_asyncio.apply()
    public_url = ngrok.connect(8000)
    print(f"Public URL: {public_url}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
