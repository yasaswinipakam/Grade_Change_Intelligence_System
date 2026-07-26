from __future__ import annotations
import json, time, joblib
from collections import deque
from pathlib import Path
import numpy as np
from simulator.config import RECIPES
from ml.shap_explanation_engine import SHAPExplanationEngine
from ml.recommendation_engine import RecommendationEngine
from ml.constraint_validation_engine import ConstraintValidationEngine

class InferenceService:
 def __init__(self, models_dir: Path, config_dir: Path):
  self.meta=json.loads((config_dir/"features.json").read_text()); self.config=json.loads((config_dir/"inference_config.json").read_text()); self.pipeline=joblib.load(models_dir/"preprocessing_pipeline.pkl"); self.reg=joblib.load(models_dir/"xgboost_regressor.pkl"); self.clf=joblib.load(models_dir/"xgboost_classifier.pkl"); self.engine=joblib.load(models_dir/"shap_explainer.pkl"); self.recommender=RecommendationEngine(); self.validator=ConstraintValidationEngine(config_dir/"constraints.json"); self.history=deque(maxlen=60)
 def _raw_feature(self,name,state):
  target=RECIPES[state["grade"]]; plain=name
  if plain.endswith("_deviation_from_grade_target"): key=plain.removesuffix("_deviation_from_grade_target"); return state[key]-target[key]
  if "_lag_" in plain:
   key,lag=plain.split("_lag_"); n=int(lag.removesuffix("m")); return self.history[-n].get(key,state[key]) if len(self.history)>=n else state[key]
  if plain.endswith("_velocity"): key=plain.removesuffix("_velocity"); return state[key]-self.history[-1].get(key,state[key]) if self.history else 0.
  if plain.endswith("_acceleration"): return 0.
  if "rolling_mean" in plain: return state[plain.split("_rolling")[0]]
  if plain.startswith("phase_"): return float(state["process_phase"]==plain.removeprefix("phase_"))
  if plain.startswith("grade_Grade "): return float(state["grade"]==plain.removeprefix("grade_"))
  if plain=="operator_action_magnitude": return 0.
  if plain=="operator_intervention_flag": return 0.
  if plain=="time_since_transition_start" or plain=="time_to_stabilization" or plain=="elapsed_ramp_percentage": return 0.
  return state.get(plain,0.)
 def decide(self,state):
  raw=np.array([[self._raw_feature(n,state) for n in self.meta["feature_columns"]]],dtype=float); scaled=self.pipeline["standard_scaler"].transform(raw)[0]
  prediction=float(self.reg.predict([scaled])[0]); probability=float(self.clf.predict_proba([scaled])[0,1]); self.history.append(dict(state)); explanation=self.engine.explain(scaled,prediction,probability); explanation.update({"timestamp":str(time.time()),"grade":state["grade"],"process_phase":state["process_phase"],"off_spec":probability>=.5}); recommendation=self.recommender.recommend(explanation); validated=self.validator.validate(recommendation)
  return {"prediction":{"basis_weight_deviation":prediction,"off_spec_probability":probability},"explanation":explanation,"recommendations":recommendation["recommendations"],"validated_recommendations":[validated]}

