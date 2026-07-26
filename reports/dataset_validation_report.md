# Dataset Validation and Quality Assurance Report

## Executive summary

**Dataset audited:** `synthetic_process_data.csv` generated with seed `42`.

**Validation verdict: FAIL — do not use this dataset for model training.**

The file is complete, finite, uniquely keyed, and stays within hard operating limits. However, it fails several gatekeeper criteria that would materially distort a predictive model:

- Grade C supplies `86.83%` of rows, exceeding the `60%` imbalance limit and leaving Grades A and B underrepresented.
- Control variables are perfectly rank-correlated because transitions move all recipe setpoints together. This is severe multicollinearity and prevents a model from distinguishing individual causal effects.
- `28,973` rows carry an operator action, including `26,921` steady-state rows. Actions should be transient events, not a persistent state label.
- `27,558` timestamp intervals exceed one minute; the maximum gap is five minutes. This follows the sparse steady-state export policy, but conflicts with the strict temporal QA expectation and must be made explicit to downstream users.
- The basis-weight-deviation mean is `2.13%`, with a maximum of `269.67%` and strong positive skew. It is not centered near zero and is not a balanced regression target.
- Risk is negatively correlated with signed basis-weight deviation (`-0.275` Spearman), contradicting the requested monotonic relation to deviation. Risk should instead be assessed against absolute deviation.

The dataset has useful structural evidence for debugging the simulator, but it is not fit for downstream training, SHAP, or recommendation evaluation until the issues below are corrected and the data regenerated.

## Audit inputs and contract

The audit used [simulator_spec.md](simulator_spec.md) as the process contract, [synthetic_process_data.csv](synthetic_process_data.csv) as the source data, and [generation_report.md](generation_report.md) for generation context. The specification defines the canonical variable ranges, three grades, hard limits, a `70–90%` success band, transition phases, calibrated delays, and an export policy that retains steady-state records every five minutes while retaining transition records each minute.

## Data quality assessment

| Check | Result | Verdict | Finding |
|---|---:|---|---|
| Records | `30,000` | PASS | Meets the approximate requested dataset size. |
| Columns | `42` | PASS | Required state, observed, target, risk, action, and label fields are present. |
| Missing values | `0` | PASS | Completeness is `100%`. |
| Duplicate timestamps | `0` | PASS | Timestamp key is unique. |
| Duplicate rows | `0` | PASS | No copy/paste duplication detected. |
| Strictly increasing timestamps | yes | PASS | No backward time movement. |
| Maximum timestamp gap | `5 min` | WARNING | Consistent with sparse steady-state export but fails a strict one-minute continuity expectation. |
| Gaps above one minute | `27,558` | WARNING | Nearly all steady-state exports are sparse by design. |
| NaN or infinite numeric values | `0` | PASS | Numeric payload is finite. |

### Variable-range assessment

All latent process variables remain inside the hard ranges in the specification. This is a meaningful positive result: clamping and numerical integration did not create physically impossible values.

| Variable | Min | Max | Mean | Std. dev. | Contract range | Verdict |
|---|---:|---:|---:|---:|---|---|
| `Q_feed` | `85.000` | `180.000` | `170.610` | `25.275` | `50–200` | PASS |
| `C_feed` | `0.700` | `1.300` | `1.238` | `0.163` | `0.5–1.5` | PASS |
| `V_line` | `750.000` | `1000.000` | `777.212` | `70.216` | `100–2000` | PASS |
| `P_heat` | `6.000` | `8.000` | `7.794` | `0.544` | `1–10` | PASS |
| `P_aux` | `3.000` | `5.000` | `4.794` | `0.544` | `0–8` | PASS |
| `Q_recycle` | `25.000` | `45.000` | `27.065` | `5.440` | `0–100` | PASS |
| `Q_add` | `10.000` | `20.000` | `18.967` | `2.720` | `0–80` | PASS |
| `E_extract` | `65.000` | `75.000` | `66.033` | `2.720` | `50–90` | PASS |
| `R_aid` | `3.000` | `6.000` | `5.662` | `0.863` | `0–12` | PASS |
| `F_inert` | `15.000` | `25.000` | `23.967` | `2.720` | `0–60` | PASS |
| `W` | `52.707` | `228.586` | `201.286` | `45.852` | `30–300` | PASS |
| `M` | `5.000` | `7.000` | `6.795` | `0.546` | `4–10` | PASS |
| `H` | `85.665` | `246.007` | `222.936` | `42.238` | `70–300` | PASS |
| `T_prod` | `75.000` | `95.000` | `92.948` | `5.494` | `20–140` | PASS |
| `D_supply` | `0.800` | `1.200` | `0.999` | `0.117` | `0.80–1.20` | PASS |
| `D_act` | `0.775` | `1.000` | `0.974` | `0.020` | `0.75–1.00` | PASS |
| `A_sensor` | `0.000` | `1.000` | `0.990` | `0.100` | `0–1` | PASS |

No latent variable is zero variance. `A_sensor` is near-zero variance relative to its full binary range; this is expected from the specified low dropout frequency and should be treated as an optional reliability feature rather than a primary model feature.

## Physics consistency assessment

### Causal relationship verification

Spearman coefficients use all rows. Each p-value was numerically below reporting precision (`p < 0.001`). Sign agreement is necessary but not sufficient: correlations inflated by grade composition and perfectly co-ramped controls are flagged separately under ML readiness.

| Relationship | Contract sign | Spearman r | Verdict | Interpretation |
|---|---|---:|---|---|
| `Q_feed → W` | positive | `0.586` | PASS | Strong enough positive aggregate association. |
| `C_feed → W` | positive | `0.586` | PASS | Sign agrees, but perfectly tied to recipe flow. |
| `V_line → W` | negative | `-0.586` | PASS | Sign agrees. |
| `Q_feed → M` | positive | `0.915` | PASS | Sign agrees; strongly recipe-driven. |
| `V_line → M` | positive | `-0.915` | FAIL | Wrong aggregate sign; grade composition dominates intended within-grade effect. |
| `P_heat → M` | negative | `0.915` | FAIL | Wrong aggregate sign; a critical thermal relationship is reversed globally. |
| `P_aux → M` | negative | `0.915` | FAIL | Wrong aggregate sign. |
| `Q_add → M` | positive | `0.915` | PASS | Sign agrees but is perfectly collinear with grade. |
| `E_extract → M` | negative | `-0.915` | PASS | Sign agrees. |
| `R_aid → W` | positive | `0.586` | PASS | Sign agrees but is recipe-confounded. |
| `F_inert → W` | negative | `0.586` | FAIL | Wrong aggregate sign. |
| `W → H` | positive | `0.991` | WARNING | Direction is correct, but near-perfect dependence makes it redundant for ML. |

**Physics verdict: FAIL.** The process equations encode several intended signs locally, but the generated dataset does not preserve all required signs after aggregation. The generator must create within-grade excitation and independently perturbed control inputs so that causal effects are observable rather than masked by grade selection.

### Dynamics, overshoot, and stabilization

The canonical model declares a weight input delay of `1 min`, moisture response on the `3–5 min` scale, and monotonic first-order response. The CSV does not include raw setpoint-change identifiers, planned transition duration, or a per-transition identifier. Therefore exact response-onset, overshoot, and stabilization measurements cannot be reliably segmented for a representative sample of transitions. This is a traceability failure, not proof that the numerical dynamics are wrong.

Observed transition phase counts are: ramp `1,461`, transient `270`, stabilization `630`, recovery `80`, and steady state `27,559`. The transient phase is consistently three records per detected transition, which is compatible with the scheduler. Recovery is present only for fault-affected transitions.

The next generator revision must export `transition_id`, `planned_duration_minutes`, previous and destination grade, and all setpoint values. Then QA can measure onset, monotonicity, overshoot, and settling directly against the specification’s calibrated delays.

### Phase and temporal consistency

The permitted exported phases are present: `steady_state`, `ramp`, `transient`, `stabilization`, and `recovery`. No invalid phase string is present. However, operator labels persist long after the action event, producing `26,921` action-bearing steady-state records. This fails the phase/action contract: actions must occur during transition phases, with a timestamped event record rather than a sticky current-state label.

## Dataset behavior assessment

### Transition duration and success

The generation report records `90` transitions and a transition-success rate of `88.89%`, which is inside the `70–90%` contract band. The CSV alone cannot reconstruct individual planned durations because it lacks transition identifiers and stable end markers. The observed ramp records are compatible with durations in the configured `10–22 min` range, but this cannot be certified transition by transition.

| Measure | Result | Verdict |
|---|---:|---|
| Reported transitions | `90` | PASS |
| Reported success rate | `88.89%` | PASS |
| Success band | `70–90%` | PASS |
| Recovered transition count | not exportable as an event count | WARNING |
| Individual duration verification | not reconstructable | FAIL |

### Off-spec excursions

| Measure | Result | Verdict |
|---|---:|---|
| Off-spec rows | `2,311` | WARNING |
| Off-spec share | `7.70%` | WARNING: exceeds the requested under-`5%` expectation but below the severe `20%` threshold. |
| Mean recorded excursion duration | `21.57 min` | FAIL: exceeds expected `1–10 min`. |
| Maximum excursion duration | `260 min` | FAIL: sustained excursion is unrealistic under the stated recovery design. |
| Off-spec steady-state rows | `596` | WARNING: should be rare; requires investigation. |

Off-spec rows occur in ramp, transient, stabilization, recovery, and steady-state phases. The very long maximum duration indicates the duration accumulator survives across sparse export boundaries and/or does not reset correctly when an action has been applied.

### Basis-weight deviation distribution

| Statistic | Value |
|---|---:|
| Mean | `2.129%` |
| Standard deviation | `29.212%` |
| Minimum | `-73.849%` |
| Fifth percentile | `-4.615%` |
| Median | `-0.614%` |
| Ninety-fifth percentile | `3.753%` |
| Maximum | `269.670%` |
| Skewness | `6.710` |
| Excess kurtosis | `54.052` |

**Verdict: FAIL.** The central bulk is near target, but rare extreme excursions create a severe right tail and pull the mean outside the requested near-zero expectation. The target is numerically non-constant and suitable in principle for regression, but should not be trained on until the extreme excursion mechanism is corrected or explicitly modeled.

### Risk-score validation

Risk stays in the required `0–100` interval. It has Spearman correlation `0.462` with `off_spec`, so it does rise for some bad conditions. But it has Spearman correlation `-0.275` with the signed basis-weight-deviation target, not the required positive monotonic relationship. This is expected from the specification’s absolute-deviation formula: risk should be tested against `abs(basis_weight_deviation)`, not the signed value. The QA requirement is therefore mismatched to the implementation contract.

**Verdict: WARNING.** Preserve the absolute-deviation risk formula, but change downstream QA to evaluate absolute deviation or export an explicit `absolute_weight_deviation` feature.

## Grade and operator analysis

| Grade | Rows | Share | Verdict |
|---|---:|---:|---|
| Grade A | `2,292` | `7.64%` | FAIL: below `15%`. |
| Grade B | `1,660` | `5.53%` | FAIL: below `15%`. |
| Grade C | `26,048` | `86.83%` | FAIL: above `60%`. |

The final steady-state fill is performed after the last transition and uses the final grade, explaining the extreme Grade C concentration. The generator must rotate final fill across grades or allocate a fixed per-grade steady-state quota.

Operator-action labels are `pressure_increase: 25,323`, `flow_increase: 3,650`, and `none: 1,027`. This is not a `20%` transition intervention rate in the exported data: it is persistent state annotation. Action magnitudes are numeric (`2.32–7.45%`) and within the specified `2–8%` band, but the action label must reset to `none` after the event row. Operator actions outside transition phases are a critical failure.

## ML readiness assessment

### Leakage and collinearity

There are no duplicate rows or timestamps and no missing values. However, nearly every recipe control is perfectly rank-correlated with the others. Examples include `Q_feed`/`C_feed = 1.000`, `Q_feed`/`V_line = -1.000`, `Q_feed`/`P_heat = 1.000`, and `Q_feed`/`Q_add = 1.000`. `W`/`H = 0.991` is also above the `0.95` redundancy threshold.

This means VIF would be undefined or effectively infinite for the control set; a conventional regression or tree explanation could not attribute the causal effect of one co-ramped control independently. It also creates target leakage risk: `H` is a direct equation function of `W`, so including both without time-aware feature design lets a model infer the target from a contemporaneous downstream output.

| ML check | Verdict | Required remediation |
|---|---|---|
| Constant columns | PASS | None. |
| Near-zero variance | WARNING | Treat `A_sensor` as optional reliability feature. |
| Correlation above `0.95` | FAIL | Add independent within-grade control perturbations and remove redundant features from baseline model. |
| VIF above `10` | FAIL | Perfect collinearity makes VIF non-actionable; regenerate after excitation is added. |
| Target non-constant | PASS | Keep regression target after outlier correction. |
| Contemporaneous downstream leakage | FAIL | Split features by causal availability; do not use `H` or post-process quality measurements when predicting current `W` deviation. |

## Quality metrics and scoring

| Dimension | Score | Basis |
|---|---:|---|
| Physics fidelity | `35/100` | Hard limits pass; several aggregate causal signs fail and dynamic audit is not traceable. |
| Statistical quality | `50/100` | Complete and finite, but target skew, off-spec duration, and grade imbalance are severe. |
| Transition quality | `55/100` | Success band passes; action persistence and duration traceability fail. |
| ML readiness | `15/100` | Severe multicollinearity and contemporaneous leakage risk. |
| **Overall quality** | **`39/100`** | **Below the gatekeeper threshold.** |

## Detailed findings and recommendations

1. **FAIL — reset actions after their event row.** `operator_action` and magnitude currently remain in simulator state. Record an event field only on the action minute, then set action metadata to `none`/zero on the next step.
2. **FAIL — balance grade quotas.** Allocate steady-state rows across the three grades before final CSV truncation; do not append all final-fill rows under the last active grade.
3. **FAIL — add independent, bounded within-grade excitation.** Apply specification-compliant disturbances to individual controls during steady state and transitions so controls are not perfectly co-ramped. Preserve hard limits and causal signs.
4. **FAIL — export transition audit fields.** Add `transition_id`, source/destination grade, planned duration, ramp progress, target setpoints, action timestamp, and outcome. This enables direct delay, settling, and duration QA.
5. **FAIL — investigate off-spec accumulator and extreme deviations.** Ensure `off_spec_duration_minutes` resets on recovery and that health/supply effects are bounded by recipe recovery logic.
6. **WARNING — align risk QA with the specified formula.** Test risk against absolute, not signed, weight deviation; export this derived value to make intent unambiguous.
7. **WARNING — document sparse timestamps.** Either export every simulation minute or amend QA expectations to accept the canonical five-minute steady-state sampling.

## Gatekeeper decision

```
VALIDATION VERDICT: FAIL

Do not proceed to model training. Regenerate the dataset after correcting
operator-action lifecycle, grade allocation, independent control excitation,
transition audit fields, and off-spec recovery behavior. Re-run this audit
against the regenerated CSV before training or explanation work begins.
```

---

## Revalidation addendum — corrected generator output

This addendum is authoritative for the regenerated `synthetic_process_data.csv`; it supersedes the dataset-specific counts in the earlier sections of this report. The first audit directly caused the remediation: one-row action events, balanced final quotas, transition audit fields, specification-backed within-grade excitation, and fault-reset handling were added before regeneration with the same seed.

| Corrective check | Refreshed result | Verdict |
|---|---:|---|
| Rows | `30,000` | PASS |
| Grade A / B / C rows | `10,000 / 10,000 / 10,000` | PASS |
| Missing, duplicate, or non-finite values | `0` | PASS |
| Operator actions in steady state | `0` | PASS |
| Transition audit fields | present (`transition_id`, source/destination grade, planned duration, ramp progress) | PASS |
| Reported transition success rate | `78.89%` | PASS: inside `70–90%` contract. |
| Off-spec share | `6.43%` | WARNING: above preferred under-`5%`, below severe `20%`. |
| Maximum off-spec duration | `38 min` | WARNING: improved materially from the original run but still above the expected short-excursion window. |
| Maximum timestamp gap | `5 min` | WARNING: canonical sparse steady-state export policy. |
| Control-pair maximum absolute Spearman correlation | `0.995` | FAIL: remains above `0.95` ML redundancy threshold. |

The added independent excitation improves within-grade variation but does not eliminate strong cross-grade recipe confounding. For example, aggregate coefficients remain positive for `P_heat → M` and `F_inert → W`, although their documented local signs are negative. The generator therefore still fails the strict causal-identifiability and multicollinearity criteria.

### Final Task 3 gate decision

```
VALIDATION VERDICT: FAIL

The corrected dataset is materially better and has no integrity, grade-balance,
or operator-action-lifecycle defect. It must not yet be used for causal or
explainable ML training because recipe-driven collinearity remains severe.
```

### Required next action

Revise the data-generation design to sample independently varied, physically feasible setpoints within each grade over longer windows, then compute causal checks conditioned on grade and process phase. Re-run this report after that change. Do not weaken the `|r| > 0.95` leakage/redundancy gate merely to accept the current data.

---

## Final independent-excitation revalidation

The steady-state generator was revised again to apply independent `±8%` setpoint excitation to every controllable variable for `10 min`, exactly as added to the implementation-ready specification. The regenerated dataset remains complete, finite, and exactly balanced across grades. Transition success is `80.00%`, inside the `70–90%` contract; off-spec exposure is `6.74%`, and the longest excursion is `35 min`.

The raw control set still has `37` pairs above the strict `|r| > 0.95` threshold; examples are `Q_feed/C_feed = 0.962`, `Q_feed/P_heat = 0.963`, and `Q_add/F_inert = 0.964`. This is caused by the widely separated three-grade recipe targets, not by missing random variation. Larger excitation would be a new, unsupported operating design and would increase off-spec behavior.

**Final Task 3 verdict remains `FAIL` for raw-feature ML readiness.** The data is valid for phase-aware EDA and for curated, grade-conditioned modeling only. A production-grade ML dataset requires either a formally approved broader operating-envelope design or a model contract that conditions/stratifies by grade and selects one representative from each collinear control group.

---

## Grade-aware ML contract resolution

The high-correlation review confirms that all `37` original pairs are recipe controls: flow, concentration, speed, heat pressures, recycle, moisture addition, extraction, retention aid, and inert additive. These variables move together in the approved Grade A/B/C targets. After replacing absolute controls with deviations from active-grade targets, the high-pair count for those residual controls is `0`; the maximum within-grade raw-control correlation is approximately `0.57`.

Task 4 now exports a curated grade-aware feature matrix with `54` standardized, past-only features. It includes two grade indicators with Grade A as reference, grade-target control deviations, lagged values, velocity, acceleration, rolling history, phase indicators, and selected interactions. Current weight, current thickness, risk, outcomes, and event-result fields are excluded to prevent target leakage. The matrix contains `0` missing values and `0` feature pairs above the strict `|r| > 0.95` threshold.

```
VALIDATION VERDICT: PASS WITH WARNINGS — GRADE-AWARE FEATURE CONTRACT

The raw dataset must not be used with absolute recipe controls as a single
unconditioned ML feature matrix. The curated grade-aware Task 4 feature matrix
is approved for model development, subject to reporting grade-specific metrics
and retaining the documented sparse-timestamp warning.
```
