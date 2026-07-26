from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Subdirectory paths
MODELS_DIR = ROOT / "models"
DATA_CONFIG_DIR = ROOT / "data" / "config"

# Required artifacts — checked at startup
REQUIRED_MODELS = (
    "xgboost_regressor.pkl",
    "xgboost_classifier.pkl",
    "shap_explainer.pkl",
    "preprocessing_pipeline.pkl",
)
REQUIRED_CONFIG = (
    "features.json",
    "inference_config.json",
    "constraints.json",
)

# Legacy REQUIRED tuple kept for backward-compat (startup check uses MODELS_DIR / DATA_CONFIG_DIR)
REQUIRED = REQUIRED_MODELS + REQUIRED_CONFIG

