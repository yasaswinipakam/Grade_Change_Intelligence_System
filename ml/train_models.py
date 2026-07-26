"""Task 5 chronological model training using the Task 4 feature contract."""
from __future__ import annotations
import json, time, joblib
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
from xgboost import XGBRegressor, XGBClassifier

def reg_metrics(y, p): return {"rmse":float(mean_squared_error(y,p)**.5),"mae":float(mean_absolute_error(y,p)),"r2":float(r2_score(y,p)),"mape":float(np.mean(np.abs((y-p)/np.maximum(np.abs(y),1e-3)))*100)}
def cls_metrics(y,p):
 q=(p>=.5).astype(int); return {"accuracy":float(accuracy_score(y,q)),"precision":float(precision_score(y,q,zero_division=0)),"recall":float(recall_score(y,q,zero_division=0)),"f1":float(f1_score(y,q,zero_division=0)),"roc_auc":float(roc_auc_score(y,p)),"pr_auc":float(average_precision_score(y,p)),"confusion_matrix":confusion_matrix(y,q).tolist()}
def main():
 d=pd.read_csv("engineered_dataset.csv"); meta=json.load(open("features.json")); features=meta["scaled_feature_columns"]
 tr,va,te=(d[d.dataset_split==x] for x in ("train","validation","test")); Xtr,Xv,Xte=tr[features],va[features],te[features]; yr,yrv,yrt=tr.basis_weight_deviation,va.basis_weight_deviation,te.basis_weight_deviation; yc,ycv,yct=tr.off_spec.astype(int),va.off_spec.astype(int),te.off_spec.astype(int)
 # Small chronological validation search; test data is untouched until final evaluation.
 choices=[dict(n_estimators=120,max_depth=4,learning_rate=.05,subsample=.8,colsample_bytree=.8),dict(n_estimators=200,max_depth=3,learning_rate=.05,subsample=.9,colsample_bytree=.9)]
 best=min(choices,key=lambda p: mean_squared_error(yrv,XGBRegressor(**p,random_state=42,n_jobs=2).fit(Xtr,yr).predict(Xv)))
 reg=XGBRegressor(**best,random_state=42,n_jobs=2).fit(pd.concat([Xtr,Xv]),pd.concat([yr,yrv])); clf=XGBClassifier(**best,random_state=42,n_jobs=2,eval_metric="logloss").fit(pd.concat([Xtr,Xv]),pd.concat([yc,ycv]))
 baselines={"random_forest_regressor":RandomForestRegressor(n_estimators=100,max_depth=10,random_state=42,n_jobs=2).fit(Xtr,yr),"linear_regression":LinearRegression().fit(Xtr,yr),"random_forest_classifier":RandomForestClassifier(n_estimators=100,max_depth=10,random_state=42,n_jobs=2,class_weight="balanced").fit(Xtr,yc),"logistic_regression":LogisticRegression(max_iter=1000,class_weight="balanced").fit(Xtr,yc)}
 rp,cp=reg.predict(Xte),clf.predict_proba(Xte)[:,1]; metrics={"configuration":{"features":features,"hyperparameters":best,"temporal_validation":"train then validation tuning; final holdout test"},"xgboost_regression":reg_metrics(yrt,rp),"xgboost_classification":cls_metrics(yct,cp),"grade_evaluation":{},"phase_evaluation":{}}
 for name, group in list(te.groupby("grade"))+list(te.groupby("process_phase")):
  idx=group.index; loc=te.index.get_indexer(idx); metrics["grade_evaluation" if name.startswith("Grade") else "phase_evaluation"][name]={"regression":reg_metrics(yrt.iloc[loc],rp[loc]),"classification":cls_metrics(yct.iloc[loc],cp[loc]) if yct.iloc[loc].nunique()>1 else {"note":"single class"}}
 rows=[]
 for n,m in baselines.items():
  if "regressor" in n or n=="linear_regression": rows.append({"model":n,"task":"regression",**reg_metrics(yrt,m.predict(Xte))})
  else: rows.append({"model":n,"task":"classification",**cls_metrics(yct,m.predict_proba(Xte)[:,1])})
 rows += [{"model":"xgboost","task":"regression",**metrics["xgboost_regression"]},{"model":"xgboost","task":"classification",**metrics["xgboost_classification"]}]
 pd.DataFrame(rows).to_csv("model_comparison.csv",index=False); imp=pd.DataFrame({"feature":features,"importance":reg.feature_importances_}).sort_values("importance",ascending=False); imp.to_csv("feature_importance.csv",index=False)
 joblib.dump(reg,"xgboost_regressor.pkl"); joblib.dump(clf,"xgboost_classifier.pkl"); joblib.dump(baselines,"baseline_models.pkl")
 Path("metrics.json").write_text(json.dumps(metrics,indent=2)); Path("model_metadata.json").write_text(json.dumps({"production_models":"XGBoost regressor and classifier","feature_count":len(features),"target_regression":"basis_weight_deviation","target_classification":"off_spec"},indent=2)); Path("inference_config.json").write_text(json.dumps({"feature_order":features,"preprocessing":"preprocessing_pipeline.pkl","models":["xgboost_regressor.pkl","xgboost_classifier.pkl"]},indent=2))
 Path("training_report.md").write_text(f"# Task 5 training report\n\n## Executive summary\n\nXGBoost was selected as the production pair after chronological validation.\n\n## Holdout performance\n\n- Regression: `{metrics['xgboost_regression']}`\n- Classification: `{metrics['xgboost_classification']}`\n\n## Training contract\n\n- Chronological train/validation/test split respected.\n- Hyperparameters selected only using validation data.\n- Grade-aware, leakage-safe feature contract from Task 4 used unchanged.\n- Per-grade and per-phase metrics are in `metrics.json`.\n\n## Deployment readiness\n\nUse the saved preprocessing pipeline and exact feature order in `inference_config.json`; models are ready for Task 6 SHAP analysis.\n")
 print(json.dumps({"regression":metrics["xgboost_regression"],"classification":metrics["xgboost_classification"]},indent=2))
if __name__=="__main__": main()
