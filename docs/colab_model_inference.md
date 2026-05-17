# Colab Model Inference

Backend local remains the main API for the frontend, MySQL, auth, products, and interactions. Colab only runs GRU4Rec inference and returns `item_id` plus `score`.

## Flow

```text
Frontend
  -> Backend local
  -> Colab model API through Ngrok
  -> Backend local enriches items from MySQL/artifacts
  -> Frontend displays recommendations
```

## Run The Colab Model API

Upload or copy these files to Colab:

- `ml/colab_model_api.py`
- `ml/checkpoints/GRU4Rec_best.pt`
- `ml/checkpoints/model_artifacts.pkl`

Install dependencies:

```bash
pip install fastapi uvicorn pyngrok nest_asyncio torch
```

Run:

```bash
python colab_model_api.py
```

Copy the printed Ngrok URL.

## Configure Local Backend

Update `backend/.env`:

```env
USE_COLAB_MODEL=true
COLAB_MODEL_API_URL=https://xxxxx.ngrok-free.app
COLAB_MODEL_TIMEOUT_SECONDS=8
```

Restart the local backend after changing `.env`.

If Colab or Ngrok is unavailable, the backend automatically falls back to the local hybrid recommender.
