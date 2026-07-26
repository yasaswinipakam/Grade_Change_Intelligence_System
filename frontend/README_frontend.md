# Honeywell Forge Decision Support Dashboard

## Setup

Run `npm install`, then `npm run dev` inside `frontend/`. The dashboard expects the FastAPI backend at `http://localhost:8000`; override it with `VITE_API_URL` if needed.

Start the backend from the project root with `uvicorn backend.app:app --reload`.

The dashboard uses `POST /decision-support` for operator decisions and `GET /health` for readiness. Use the healthy and high-risk sample buttons for the presentation demo.
