import torch
import torch.nn as nn
import torch.nn.utils.rnn as rnn_utils

class GRU4Rec(nn.Module):
    def __init__(self, num_items, emb_dim=64, hidden=128, n_layers=1, dropout=0.2):
        super().__init__()
        self.hidden    = hidden
        self.embedding = nn.Embedding(num_items+1, emb_dim, padding_idx=0)
        self.gru       = nn.GRU(emb_dim, hidden, n_layers, batch_first=True)
        self.dropout   = nn.Dropout(dropout)
        self.fc        = nn.Linear(hidden, emb_dim)

    def forward(self, item_seq, seq_len):
        emb    = self.dropout(self.embedding(item_seq))
        packed = rnn_utils.pack_padded_sequence(
            emb, seq_len.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.gru(packed)
        out, _ = rnn_utils.pad_packed_sequence(out, batch_first=True)
        
        idx    = (seq_len-1).long().unsqueeze(1).unsqueeze(2).expand(-1,1,self.hidden)
        last   = out.gather(1, idx.to(out.device)).squeeze(1)
        return self.fc(self.dropout(last))

    def predict_topk(self, item_seq, seq_len, top_k=10, exclude_ids=None):
        with torch.no_grad():
            out    = self.forward(item_seq, seq_len)
            all_e  = self.embedding.weight[1:]
            scores = (out @ all_e.T).squeeze(0)
            if exclude_ids:
                for eid in exclude_ids:
                    if 1 <= eid <= scores.size(0):
                        scores[eid-1] = -1e9
            topk_sc, topk_idx = torch.topk(scores, top_k)
            return (topk_idx + 1).tolist(), topk_sc.tolist()
