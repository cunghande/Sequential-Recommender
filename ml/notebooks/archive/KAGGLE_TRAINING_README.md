# Kaggle training guide

Use `kaggle_seqrec_training_notebook.ipynb` on Kaggle. It has real notebook cells, so charts, tables, `display(...)`, and `plt.show()` outputs appear directly under each cell.

`kaggle_seqrec_training_notebook.py` is kept as the editable source version.

## How to run

1. Create a Kaggle notebook and enable GPU.
2. Add the Amazon Video Games review + metadata dataset.
3. Import or upload `kaggle_seqrec_training_notebook.ipynb`.
4. Check these two files are found in the setup cell:
   - `Video_Games.jsonl`
   - `meta_Video_Games.jsonl`
   - The notebook still supports `.jsonl.gz` as a fallback if you use compressed files later.
5. If Kaggle uses a different input folder, edit:
   - `REVIEW_FILE_CANDIDATES`
   - `META_FILE_CANDIDATES`
6. Run all cells.

Do not paste the whole `.py` file into one Kaggle cell for the report run. Kaggle may not split `# %%` markers into notebook cells correctly.

## Fast test vs real report run

The notebook has:

```python
RUN_FAST_SMOKE = False
```

Keep it `False` for the real report run. Set it to `True` only when you want a quick syntax/runtime check.

## Files to download after training

Download `seqrec_kaggle_exports.zip` or these files from `exports/`:

- `GRU4Rec_best.pt`
- `LSTM_best.pt`
- `model_artifacts.pkl`
- `metrics_summary.csv`
- `training_history.csv`
- `preprocessing_stats.csv`
- `web_export.json`

For the local demo, copy these into:

```text
D:/Project_Root/checkpoints/
```

The backend now loads `GRU4Rec_best.pt` first and falls back to `GRU4Rec_final.pt` if the best checkpoint is not present.

## Report tables

Use these generated CSV files:

- `metrics_summary.csv`: model comparison table.
- `preprocessing_stats.csv`: before/after preprocessing table.
- `training_history.csv`: tuning history for LSTM/GRU4Rec.

Use these generated charts from `outputs/`:

- `01_rating_distribution.png`
- `02_sequence_length.png`
- `03_top_categories.png`
- `04_hr10_model_comparison.png`
- `05_ndcg10_model_comparison.png`
- `06_val_ndcg10_by_epoch.png`
- `07_training_loss.png`
