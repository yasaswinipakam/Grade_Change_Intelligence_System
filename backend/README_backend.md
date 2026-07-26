# Backend API

Run `uvicorn backend.app:app --reload`. Use `/docs` for OpenAPI. The primary endpoint is `POST /decision-support`; it accepts the fields in `ProcessRequest` and returns prediction, SHAP explanation, Task 7 recommendations, and Task 8 validated recommendation objects.
