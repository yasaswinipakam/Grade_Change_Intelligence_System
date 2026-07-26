# Grade Change Intelligence System

<div align="center">

![Grade Change Intelligence System](assets/architecture.png)

*A human-in-the-loop decision-support prototype for industrial paper-machine grade transitions*

[![GitHub Repo](https://img.shields.io/badge/GitHub-Grade_Change_Intelligence_System-181717?style=for-the-badge&logo=github)](https://github.com/yasaswinipakam/Grade_Change_Intelligence_System)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML_Model-FF6600?style=for-the-badge)](https://xgboost.readthedocs.io)

🔗 **[https://github.com/yasaswinipakam/Grade_Change_Intelligence_System](https://github.com/yasaswinipakam/Grade_Change_Intelligence_System)**

> **Prototype boundary:** This system uses synthetic data and is not deployed, validated on a production mill, or capable of autonomously controlling equipment. It is a human-in-the-loop decision-support prototype.

</div>

---

## Project Overview

**Grade Change Intelligence** is a human-in-the-loop decision-support prototype for manufacturing grade transitions. A physics-inspired simulator creates traceable synthetic process data; grade-aware XGBoost models estimate basis-weight deviation and off-spec risk; TreeSHAP explains the prediction drivers in operator language; and a separate constraint gate approves, modifies, or rejects feasible operator actions before they reach the dashboard. The whole path — from process state to validated recommendation — is transparent and auditable.

Grade transitions are difficult because multiple controls move together, process responses are delayed, and poor coordination creates off-spec material. This project uses literature-supported causal directions (feed flow and consistency increasing basis weight; line speed reducing it) to build a transparent simulator rather than pretending to have plant historian data. The ML pipeline residualizes controls against each grade recipe, engineers lags and rates of change, and preserves strict time order in train/validation/test splits. XGBoost predicts deviation and risk; TreeSHAP produces local signed explanations; the recommendation engine maps only controllable SHAP drivers toward the active grade target; and the constraint validation engine checks grade targets, operating limits, direction, and phase-dependent step size before any action surfaces to the operator.

The user-facing layer is a React + TypeScript dashboard served by a FastAPI backend. Operators interact with a live risk gauge, SHAP-driver panel, ranked recommendations with constraint status, and a historical-evidence panel. The entire pipeline is deterministic, reproducible with a fixed seed, and independently testable module by module.

---

## Problem Statement

Industrial paper-machine grade changes are high-risk events in which out-of-spec production can waste thousands of kilograms of raw material and delay delivery schedules by hours. Controls interact: flow, consistency, retention, and speed all affect basis weight with delays and nonlinearities. Operators historically rely on intuition and static runbooks, with little real-time guidance on which parameters are drifting, how severe the quality impact will be, or which corrective action is safe and feasible. Literature reviewed in this project reports that model-based grade-change control reduced a cited transition from twenty-two to ten minutes — the project does **not** claim to reproduce that improvement on a real machine, but that evidence motivates the problem and the design of this prototype.

---

## Truth Boundary

| Category | What is true in this project |
|---|---|
| **Implemented** | Physics-inspired simulator, synthetic dataset, grade-aware features, XGBoost models, SHAP explanations, recommendation + constraint pipeline, FastAPI API, React dashboard |
| **Literature-supported** | Qualitative causal directions; nonlinear/time-delayed dynamics; grade-change evidence of ~10–22 minutes; need for explainable, operator-in-the-loop decision support |
| **Engineering assumptions** | Operating ranges, symbolic gains, noise, phase labels, recipes, disturbance patterns, actuator step caps, and synthetic historical evidence |
| **Future work** | Plant historian integration, external validation, calibrated uncertainty, formal safety review, counterfactual optimisation, authentication, audit persistence, deployment hardening |

---

## Features

| Feature | Description |
|---|---|
| 🔬 **Research-informed simulator** | Physics-inspired Forward-Euler simulator generates 30,000 labelled rows across 90 grade transitions with calibrated noise, discrete interventions, and phase tagging (ramp / transient / stabilization / recovery / steady state) |
| ⚙️ **Grade-aware feature engineering** | 52-feature pipeline: grade residuals, temporal lags (5 / 15 / 60 min), velocity, acceleration, interactions, phase + grade one-hot encoding — residuals prevent recipe identity from masquerading as a control signal |
| 🌲 **XGBoost prediction** | Chronological-split trained regressor (basis-weight deviation) and classifier (off-spec flag); `n_estimators=120`, `max_depth=4`, `lr=0.05`, `subsample=0.8`, `colsample_bytree=0.8` |
| 🔍 **TreeSHAP explainability** | Local signed SHAP contributions per prediction; global beeswarm importance plot; operator-language messages per driver — SHAP explains the model's learned association, not physical causality |
| 💡 **Recommendation engine** | Maps actionable SHAP contributors to controllable process variables; recommends direction toward active grade target; de-duplicates and ranks by local impact and confidence |
| ✅ **Constraint validation** | Checks controllability, grade target, operating limit, direction, phase-dependent step cap, and conflicts — outputs `APPROVED`, `MODIFIED`, or `REJECTED` with full traceability |
| ⚛️ **React dashboard** | Live risk gauge, basis-weight trend, SHAP driver panel, recommendation + constraint status, historical evidence; scenario selector for demonstration; collapsible advanced controls |
| 🚀 **FastAPI backend** | `/decision-support`, `/health`, `/predict`, `/explain`, `/recommend` — artifacts load once at startup; Pydantic validates all inputs; CORS limited to local development origins |

---

## Architecture

![System Architecture](assets/architecture.png)

The architecture is layered and separation-of-concerns driven. Raw sensor data flows through the feature-engineering pipeline into the XGBoost prediction stack. Outputs are enriched by the SHAP explanation engine, then passed to the recommendation engine. The constraint validation engine acts as a feasibility gate — independent of both the model and the recommender — before the validated action is served through FastAPI to the React dashboard. Prediction, explanation, recommendation, and safety validation are kept as separate, independently testable responsibilities.

---

## Workflow

![System Workflow](assets/workflow.png)

The end-to-end workflow: the physics-inspired simulator generates labelled process data → feature engineering extracts grade-relative predictive signals → XGBoost models are trained on a chronological split → at inference, a live process snapshot is engineered, predicted, explained with TreeSHAP, ranked by the recommendation engine, validated by the constraint gate, and displayed on the operator dashboard.

---

## Dashboard

![Dashboard — Overview](assets/dashboard_1.png)

*Live risk gauge, basis-weight trend, and transition progress panel*

![Dashboard — Recommendations](assets/dashboard_2.png)

*Ranked recommendations with confidence scores and constraint-validation status (`APPROVED` / `MODIFIED` / `REJECTED`)*

![Dashboard — SHAP Explanations](assets/dashboard_3.png)

*Per-prediction signed SHAP contributors with operator-language messages and raw feature traceability*

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+

### Python dependencies

```bash
pip install -r requirements.txt
```

### Backend

From the project root (activate your virtual environment first):

```bash
source venv/bin/activate
uvicorn backend.app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (default: `http://localhost:5173`).  
Interactive API docs: `http://localhost:8000/docs`

---

## Results

### Regression — basis-weight deviation

| Metric | Value | Interpretation |
|---|---|---|
| **RMSE** | **0.1467** | Primary error metric on the synthetic chronological holdout |
| **MAE** | 0.0252 | Average absolute deviation; more interpretable than RMSE |
| **R²** | **0.877** | Explains 87.7 % of variance in basis-weight deviation on this holdout |
| MAPE | 930.6 % | **Not meaningful** — target can be near zero; MAPE is unstable here; report as a known limitation |

### Classification — off-spec flag

| Metric | Value | Interpretation |
|---|---|---|
| **ROC-AUC** | **0.998** | Strong ranking signal on this holdout; not proof of calibrated deployment probability |
| PR-AUC | 0.125 | More informative under imbalance; modest because positives are rare |
| Accuracy | 99.5 % | Misleading — dominated by the majority class |
| Precision | 0.08 | Many alerts are false positives relative to only **two** true positives in the holdout |
| Recall | 1.00 | Both positives were found; sample count too small for a strong claim |
| F1 | 0.148 | Warns against relying on accuracy alone |

**Confusion matrix:** `TN=4475 | FP=23 | FN=0 | TP=2`

> The holdout contains only two positive (off-spec) labels. These metrics demonstrate that the system correctly identifies the rare events present in synthetic data, but **do not indicate production readiness**. External validation, additional positive examples, class balancing, threshold calibration, and prospective evaluation are required.

### SHAP explainability

The top global driver is **`z_Q_feed_deviation_from_grade_target`** (mean |SHAP| = 1.469), confirming that stock-flow distance from the target grade setpoint dominates predictions. Line-speed velocity (`z_V_line_velocity`, mean |SHAP| = 0.491) and additive-flow deviation (`z_Q_add_deviation_from_grade_target`, mean |SHAP| = 0.448) rank second and third. SHAP values explain the **model's learned association** — not physical causality and not a guaranteed intervention effect.

![SHAP Summary Plot](outputs/shap_plots/shap_summary_plot.png)

### Recommendation and constraint validation

The recommendation engine generated validated corrective actions for all 90 simulated transitions. The constraint gate outputs one of `APPROVED`, `MODIFIED`, or `REJECTED` with reason, constraint trigger, and execution readiness — configuration limits are simulator assumptions and would require engineering authority and formal management of change in a real system.

---

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `simulator/` | Generate process trajectories with causal structure, phases, noise, and interventions |
| `ml/feature_engineering.py` | Leakage-safe grade-aware features; residuals prevent recipes from dominating the model |
| `ml/train_models.py` | Chronological train/validation/test split; saved preprocessing makes inference reproducible |
| `explanation_engine.py` | TreeSHAP local signed attributions for XGBoost predictions |
| `ml/recommendation_engine.py` | SHAP-linked actions; only controllable variables; full traceability to prediction ID and SHAP values |
| `ml/constraint_validation_engine.py` | Feasibility gate — separate from usefulness; independently testable |
| `backend/` | Artifact loading at startup; thin endpoint routes; Pydantic schema validation |
| `frontend/` | Operator interface; displays evidence first; no actuator write-back path |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Synthetic data | Necessary to demonstrate the pipeline without authorized plant data; limitations are explicit |
| Physics-inspired simulator | Preserves causal signs and delayed behavior better than arbitrary random data |
| Grade residuals | Prevent recipe identity from masquerading as a control signal |
| XGBoost | Strong tabular baseline with nonlinear interactions and native TreeSHAP compatibility |
| Random Forest baseline | Sanity-check ensemble baseline retained in `models/baseline_models.pkl` |
| No LSTM / Transformer | Insufficient real sequential data; explainability/complexity mismatch for this prototype |
| SHAP | Local and global signed explanations for tree models; not treated as causality |
| Separate recommendation and constraint engines | Keeps usefulness, feasibility, and safety responsibilities auditable and independently testable |
| FastAPI | Typed schemas, startup artifact loading, OpenAPI docs, modular services |
| Human in the loop | Recommendations are **not** actuator commands; operator and engineering authority remain required |

---

## Project Structure

```
Grade Change Intelligence System/
│
├── backend/                          # FastAPI application
│   ├── app.py                        # Router, lifespan, and API endpoints
│   ├── services.py                   # InferenceService business logic
│   ├── schemas.py                    # Pydantic request/response models
│   ├── config.py                     # Path config (models/, data/config/)
│   └── __init__.py
│
├── frontend/                         # React + TypeScript dashboard (Vite)
│   ├── src/
│   │   ├── pages/Dashboard.tsx       # Main dashboard page
│   │   ├── components/               # UI panels, forms, status bar
│   │   ├── services/api.ts           # Backend API client
│   │   ├── types/api.ts              # TypeScript type definitions
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── tsconfig.json
│
├── ml/                               # ML pipeline package
│   ├── feature_engineering.py        # 52-feature engineering pipeline
│   ├── train_models.py               # XGBoost training with temporal split
│   ├── prediction_engine.py          # Deterministic inference engine
│   ├── prediction_feature_processor.py # 15-feature inference processor
│   ├── shap_explanation_engine.py    # TreeSHAP local + global explanations
│   ├── recommendation_engine.py      # SHAP-linked corrective action generator
│   ├── constraint_validation_engine.py # Feasibility gate (APPROVED/MODIFIED/REJECTED)
│   ├── historical_evidence_engine.py # Comparable-transition evidence lookup
│   └── __init__.py
│
├── simulator/                        # Physics-inspired grade-change simulator
│   ├── process_simulator.py          # Forward-Euler dynamics simulator
│   ├── dataset_generator.py          # Dataset generation orchestrator
│   ├── transition_scheduler.py       # Grade transition scheduling
│   ├── config.py                     # Grade recipes and simulator constants
│   ├── csv_exporter.py               # Output CSV writer
│   ├── validation_engine.py          # Causal-sign and range validation
│   └── __init__.py
│
├── services/                         # Shared service layer
│   ├── explanation_service.py
│   ├── feedback_service.py
│   ├── prediction_service.py
│   └── recommendation_service.py
│
├── data/                             # All data files
│   ├── raw/
│   │   └── synthetic_process_data.csv   # Generated training data (30,000 rows, gitignored)
│   ├── processed/
│   │   └── engineered_dataset.csv       # Feature-engineered dataset (52 features, gitignored)
│   └── config/
│       ├── constraints.json             # Recipe and machine-safety limits
│       ├── features.json                # Feature column definitions (gitignored)
│       ├── feature_statistics.json      # Feature summary statistics (gitignored)
│       └── inference_config.json        # Inference pipeline configuration (gitignored)
│
├── models/                           # Trained model artifacts (gitignored)
│   ├── xgboost_regressor.pkl
│   ├── xgboost_classifier.pkl
│   ├── shap_explainer.pkl
│   ├── preprocessing_pipeline.pkl
│   ├── baseline_models.pkl
│   ├── metrics.json
│   ├── model_metadata.json
│   └── model_comparison.csv
│
├── outputs/                          # Generated inference outputs (gitignored)
│   ├── local_explanations.json
│   ├── validated_recommendations.json
│   ├── recommendation_examples.json
│   └── shap_plots/
│       ├── shap_summary_plot.png
│       └── dependence/               # Per-feature SHAP dependence plots
│
├── assets/                           # Project media and diagrams
│   ├── architecture.png
│   ├── workflow.png
│   ├── dashboard_1.png
│   ├── dashboard_2.png
│   └── dashboard_3.png
│
├── reports/                          # Generated reports and analysis docs
│   ├── dataset_validation_report.md
│   ├── deep-research-report.md
│   ├── simulator_spec.md
│   └── ...
│
├── tests/                            # Test suite (26 tests, all passing)
│   ├── conftest.py
│   ├── test_prediction_engine.py
│   ├── test_prediction_feature_processor.py
│   ├── test_shap_explanation_engine.py
│   ├── test_constraint_validation_engine.py
│   ├── test_historical_evidence_engine.py
│   └── ...
│
├── scripts/                          # Utility scripts
├── notebooks/                        # Jupyter notebooks
│   └── feature_engineering_notebook.ipynb
│
├── explanation_engine.py             # Backward-compatibility shim for shap_explainer.pkl
├── schema.sql                        # Operational DB schema (SQLite / PostgreSQL)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## References

1. **Chu et al. (2011)** — Papermaking MD control and MPC grade-change evidence; supports coupled trajectory thinking and the cited 10–22 minute transition context.
2. **Shen et al. (2023)** — Basis-weight loop is nonlinear, delayed, and time-varying; motivates lag-aware, physics-inspired dynamics.
3. **Sengupta et al. / IPPTA (1996)** — Basis weight depends on consistency, flow, retention, speed, and lag; supports causal sanity checks in the simulator.
4. **Murphy & Starr / ABB (2012)** — Practical grade-change issues, logging, and operational troubleshooting context.
5. **Yeo et al. (2005)** — Data-driven predictive control concept for grade transitions; motivates ML plus process context.
6. **Moosavi et al. (2024)** — Manufacturing XAI rationale; supports explainability as an operator trust requirement.
7. **Callicott (2025)** — Industrial recommendation-engine context and operator adoption; motivates human-in-the-loop design.
8. **Lundberg & Lee (2017)** — *A Unified Approach to Interpreting Model Predictions.* NeurIPS 2017. https://arxiv.org/abs/1705.07874
9. **Lundberg et al. (2020)** — *From local explanations to global understanding with explainable AI for trees.* Nature Machine Intelligence, 2, 56–67.
10. **Chen & Guestrin (2016)** — *XGBoost: A Scalable Tree Boosting System.* KDD '16. https://arxiv.org/abs/1603.02754
