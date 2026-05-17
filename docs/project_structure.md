# Project Structure

This repository is split into four runtime areas.

## Frontend

`frontend/` is the Next.js app. It renders the product catalog, product detail pages, cart, profile/history, and AI Picks.

Key flow:

- Product cards link to `/product/[asin]`.
- Product detail records `view`, `cart`, `like`, and `rate` interactions through the backend.
- AI Picks calls `/recommend?top_k=16&user_id=...` and displays personalized recommendations when history exists.

## Backend

`backend/` is the FastAPI API used by the frontend.

Key flow:

- Routers in `backend/app/routers/` expose auth, product, interaction, user, and recommendation endpoints.
- Thin app services in `backend/app/services/` delegate to core services.
- `backend/services/recommender.py` owns recommendation behavior: popular fallback, session history, Colab model calls, local hybrid ranking, and metadata enrichment.

## ML

`ml/` stores model artifacts and training/reference material.

Keep:

- `ml/checkpoints/GRU4Rec_best.pt`
- `ml/checkpoints/LSTM_best.pt`
- `ml/checkpoints/model_artifacts.pkl`
- `ml/notebooks/seqrec_training_pipeline.ipynb`
- `ml/colab_model_api.py`

Do not keep generated notebook outputs, archived experiments, report scripts, logs, or Python caches in source control.

## Database

`database/` stores MySQL schema and seed data. Backend reads DB settings from `backend/.env`.
