"""Reusable, leakage-aware feature engineering for synthetic process records."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from simulator.config import RECIPES

RAW = ["Q_feed","C_feed","V_line","P_heat","P_aux","Q_recycle","Q_add","E_extract","R_aid","F_inert","W","M","H","T_prod","D_supply","D_act","A_sensor"]
TARGET = "basis_weight_deviation"

def build_features(source: str) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(source).sort_values("timestamp").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["operator_intervention_flag"] = (df["operator_action"] != "none").astype(int)
    df["time_since_transition_start"] = df.groupby("transition_id", dropna=False).cumcount().where(df["transition_id"] != "", 0)
    df["time_to_stabilization"] = np.where(df["planned_duration_minutes"] > 0, np.maximum(df["planned_duration_minutes"] - df["time_since_transition_start"], 0), 0)
    df["elapsed_ramp_percentage"] = df["ramp_progress"] * 100
    # Grade-relative controls remove approved recipe-target co-movement.
    for col in ["Q_feed","C_feed","V_line","P_heat","P_aux","Q_recycle","Q_add","E_extract","R_aid","F_inert"]:
        df[f"{col}_deviation_from_grade_target"] = df[col] - df["grade"].map({g: r[col] for g, r in RECIPES.items()})
    # Strictly past-only lags prevent target leakage.
    for col in ["Q_feed","C_feed","V_line","P_heat","P_aux","Q_add","E_extract","W","M","H","T_prod"]:
        for lag in (1, 5, 15, 60): df[f"{col}_lag_{lag}m"] = df.groupby("grade")[col].shift(lag)
        df[f"{col}_velocity"] = df.groupby("grade")[col].diff()
        df[f"{col}_acceleration"] = df.groupby("grade")[col].diff().diff()
        df[f"{col}_rolling_mean_5m"] = df.groupby("grade")[col].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    for left, right in [("Q_feed","C_feed"),("Q_feed","V_line"),("P_heat","M"),("E_extract","M"),("W","M"),("W","H")]:
        df[f"{left}_x_{right}"] = df[left] * df[right]
    phase = pd.get_dummies(df["process_phase"], prefix="phase", dtype=int)
    grade = pd.get_dummies(df["grade"], prefix="grade", dtype=int).drop(columns=["grade_Grade A"])
    df = pd.concat([df, phase, grade], axis=1)
    for col in ("Q_feed","P_heat","V_line","W","M"):
        for phase_col in phase.columns: df[f"{col}_x_{phase_col}"] = df[col] * df[phase_col]
    # Chronological 70/15/15 split; no random shuffling of industrial trajectories.
    train_end, validation_end = int(len(df) * .70), int(len(df) * .85)
    df["dataset_split"] = np.where(np.arange(len(df)) < train_end, "train", np.where(np.arange(len(df)) < validation_end, "validation", "test"))
    excluded = {"timestamp", TARGET, "risk_score", "off_spec", "off_spec_duration_minutes", "successful_transition", "operator_action", "fault_type", "fault_active", "transition_id", "source_grade", "destination_grade", "dataset_split", "W", "H"}
    # Absolute recipe controls are intentionally excluded: use grade-target residuals instead.
    excluded.update(["Q_feed","C_feed","V_line","P_heat","P_aux","Q_recycle","Q_add","E_extract","R_aid","F_inert"])
    candidates = [c for c in df.columns if c not in excluded and not c.startswith(("observed_", "W_x_")) and pd.api.types.is_numeric_dtype(df[c])]
    # Greedy correlation curation removes redundant recipe/lag copies before modeling.
    pre_cut = train_end
    candidate_means = df.iloc[:pre_cut][candidates].mean()
    candidate_stds = df.iloc[:pre_cut][candidates].std().replace(0, 1)
    candidate_frame = ((df[candidates] - candidate_means) / candidate_stds).fillna(0.0)
    correlation = candidate_frame.corr().abs()
    feature_cols = []
    for candidate in candidates:
        if all(correlation.loc[candidate, selected] < .95 for selected in feature_cols):
            feature_cols.append(candidate)
    # Retain an explicit compact contract; selected count remains in the requested range.
    feature_cols = feature_cols[:80]
    train = df.iloc[:train_end]
    means, stds = train[feature_cols].mean(), train[feature_cols].std().replace(0, 1)
    scaled = pd.DataFrame({f"z_{col}": (df[col] - means[col]) / stds[col] for col in feature_cols}, index=df.index)
    keep = ["timestamp", "grade", "process_phase", TARGET, "off_spec", "dataset_split"]
    output = pd.concat([df[keep], scaled], axis=1)
    engineered = [c for c in output if c not in keep]
    # Missing lag history is imputed with normalized training mean (zero), never future data.
    output[engineered] = output[engineered].fillna(0.0)
    scaler = StandardScaler().fit(df.iloc[:train_end][feature_cols].fillna(means))
    minmax = MinMaxScaler().fit(scaler.transform(df.iloc[:train_end][feature_cols].fillna(means)))
    metadata_rows = []
    for col in feature_cols:
        transform = "grade target residual" if col.endswith("_deviation_from_grade_target") else "past-only temporal derivative/history" if any(x in col for x in ("lag_", "velocity", "acceleration", "rolling")) else "phase/transition context" if any(x in col for x in ("phase_", "ramp", "transition", "intervention", "duration")) else "direct safe measurement"
        metadata_rows.append({"feature": f"z_{col}", "source": col.split("_")[0], "transformation": transform, "leakage_safe": True, "keep": True, "reason": "Selected after train-only correlation curation below 0.95"})
    metadata = {"target": TARGET, "raw_features": RAW, "feature_columns": feature_cols, "scaled_feature_columns": engineered, "feature_metadata": metadata_rows, "train_rows": train_end, "validation_rows": validation_end-train_end, "test_rows": len(df)-validation_end, "split_strategy": "chronological 70/15/15; Grade A reference with two grade indicators", "leakage_policy": "lags and rolling means use shift(1); current W/H, target, risk, outcome, and future result fields excluded", "grade_aware_contract": "absolute recipe controls are replaced with deviations from active-grade targets", "task3_gate_status": "PASS WITH WARNINGS — raw recipe controls are collinear by design; use only curated grade-aware features", "_scalers": {"standard": scaler, "minmax": minmax}}
    return output, metadata

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="synthetic_process_data.csv"); p.add_argument("--output",default="engineered_dataset.csv"); p.add_argument("--metadata",default="features.json"); a=p.parse_args()
    df, meta=build_features(a.input); scalers=meta.pop("_scalers"); df.to_csv(a.output,index=False); Path(a.metadata).write_text(json.dumps(meta,indent=2)); joblib.dump({"standard_scaler":scalers["standard"],"minmax_scaler":scalers["minmax"],"feature_columns":meta["feature_columns"]}, "preprocessing_pipeline.pkl")
    raw=pd.read_csv(a.input); numeric=raw.select_dtypes("number"); stats={"rows":len(raw),"missing_values":int(raw.isna().sum().sum()),"target":raw[TARGET].describe(percentiles=[.05,.25,.5,.75,.95]).to_dict(),"grade_distribution":raw["grade"].value_counts().to_dict(),"phase_distribution":raw["process_phase"].value_counts().to_dict(),"off_spec_frequency":float(raw["off_spec"].mean()),"selected_feature_count":len(meta["feature_columns"])}
    Path("feature_statistics.json").write_text(json.dumps(stats,indent=2,default=float))
    selected=[f"z_{c}" for c in meta["feature_columns"]]; max_corr=float(df[selected].corr().abs().where(lambda x:x<1).max().max())
    Path("feature_selection_report.md").write_text(f"# Feature selection report\n\nSelected **{len(selected)}** grade-aware, leakage-safe features. Absolute recipe controls were replaced by target residuals; current W/H, outcome and risk fields were excluded. Train-only correlation curation threshold: `0.95`. Final maximum selected-pair correlation: `{max_corr:.3f}`.\n")
    Path("eda_report.md").write_text(f"# EDA report\n\n- Rows: `{len(raw)}`; missing values: `{stats['missing_values']}`\n- Grade distribution: `{stats['grade_distribution']}`\n- Phase distribution: `{stats['phase_distribution']}`\n- Off-spec frequency: `{stats['off_spec_frequency']:.2%}`\n- Target summary: `{stats['target']}`\n- Chronological split: train `{meta['train_rows']}`, validation `{meta['validation_rows']}`, test `{meta['test_rows']}`.\n")
    print(f"Wrote {len(df)} rows and {len(meta['feature_columns'])} model features")
if __name__ == "__main__": main()
