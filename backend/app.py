from __future__ import annotations
import logging, time, uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.config import MODELS_DIR, DATA_CONFIG_DIR, REQUIRED_MODELS, REQUIRED_CONFIG
from backend.schemas import ProcessRequest
from backend.services import InferenceService
logging.basicConfig(level=logging.INFO); log=logging.getLogger(__name__)
app=FastAPI(title="Grade Change Intelligence Backend",version="1.0")
# The React/Vite development server is a separate localhost origin.  Permit
# only local development origins so the browser can call the decision-support
# endpoints without opening the API to arbitrary websites.
app.add_middleware(
 CORSMiddleware,
 allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
 allow_credentials=False,
 allow_methods=["GET", "POST", "OPTIONS"],
 allow_headers=["Content-Type", "Authorization"],
)
@app.on_event("startup")
def startup():
 missing_models=[x for x in REQUIRED_MODELS if not (MODELS_DIR/x).exists()]
 missing_config=[x for x in REQUIRED_CONFIG if not (DATA_CONFIG_DIR/x).exists()]
 missing=missing_models+missing_config
 if missing: raise RuntimeError(f"Missing inference artifacts: {missing}")
 app.state.service=InferenceService(MODELS_DIR, DATA_CONFIG_DIR)
@app.get("/health")
def health(): return {"status":"healthy","model_loaded":hasattr(app.state,"service"),"shap_loaded":hasattr(app.state,"service"),"constraints_loaded":hasattr(app.state,"service")}
def run(request:ProcessRequest):
 request_id=str(uuid.uuid4()); start=time.perf_counter()
 try:
  result=app.state.service.decide(request.model_dump()); log.info("request_id=%s latency_ms=%.2f",request_id,(time.perf_counter()-start)*1000); return {"request_id":request_id,**result}
 except Exception as exc:
  log.exception("request_id=%s inference failed",request_id); raise HTTPException(500,detail={"error":"InferenceError","request_id":request_id,"message":str(exc)})
@app.post("/predict")
def predict(request:ProcessRequest):
 data=run(request); return {"request_id":data["request_id"],"prediction":data["prediction"]}
@app.post("/explain")
def explain(request:ProcessRequest):
 data=run(request); return {"request_id":data["request_id"],"explanation":data["explanation"]}
@app.post("/recommend")
def recommend(request:ProcessRequest):
 data=run(request); return {"request_id":data["request_id"],"recommendations":data["recommendations"]}
@app.post("/decision-support")
def decision_support(request:ProcessRequest): return run(request)

