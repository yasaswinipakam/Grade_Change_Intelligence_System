# Simulator Implementation Blocker

## Status

**Superseded.** The implementation-ready calibration amendment in [simulator_spec.md](simulator_spec.md) resolves the missing-coefficient, disturbance, risk, fault, and canonical dataset-plan gaps recorded below. This file is retained as a trace of the earlier specification review; it is not a current implementation blocker.

## Blocking gaps in `simulator_spec.md`

| Required to execute the requested simulator | Specification status | Why implementation cannot proceed |
|---|---|---|
| Numerical `gain_*` coefficients in the weight, moisture, thickness, and temperature equations | Symbolic only | The specification explicitly says all coefficients must be calibrated and that no numerical ODE coefficient is authorized. Forward Euler integration still requires values for every gain. |
| Numerical `tau_*` values | Symbolic only | Response-time ranges are present, but no mapping from a selected response time to each equation’s time constant is authorized. Selecting a midpoint or any calibration rule would be a new engineering assumption. |
| `base_moisture`, `base_thickness`, and `ambient_temperature` | Symbolic only | Each appears in a model equation but has no numerical value or allowed derivation. |
| `retention_effect` model | Symbolic only | It appears in the weight equation without a defined equation, state update, or numeric parameter. |
| Noise sampling distribution parameters | Partial | Magnitudes exist, but the mapping from stated `±` bands to Gaussian standard deviations is not specified. Choosing whether the band means one, two, or three standard deviations would be an invention. |
| Supply and actuator random-walk innovations | Missing | The equations use `eta_supply` and `eta_actuator`, but no distribution, rate, or update policy is specified. |
| Fault dynamics and recovery dynamics | Missing | The specification says faults can override health/availability but does not define fault types, duration, recovery trajectory, or outcome labeling policy. |
| Risk-score formula | Missing | The task requires a score from multiple indicators but forbids hardcoding it. The specification contains no risk-score equation, weights, thresholds, or historical-precedent model. |
| Complete off-spec-duration behavior | Missing | Recipe windows exist, but no precise accumulator reset rule is supplied for tolerances, recovery, and phase changes. |
| Exact transition outcome policy | Partial | The success criterion exists, but failure and recovery generation probabilities and the required corrective-action policy are undefined. |

## Direct conflicts between this task and the source-of-truth specification

| Topic | Task request | `simulator_spec.md` | Required resolution |
|---|---|---|---|
| Dataset volume | Three months and approximately `30,000` records | `90 days` at `1 min`, explicitly calculated as `129,600` rows | Select one output-size requirement or amend the sampling plan. |
| Transitions | Default range `500–1000` | `60–120` transitions | Select one range; both cannot describe the same specified dataset. |
| Operator-action frequency | `20%` of transitions | `25%` of transitions | Select one percentage. |
| Warm-up | `500` equilibrium timesteps | No warm-up duration | Add this as a documented design choice to the specification, or remove it. |
| Public step inputs | `Q1_sp`, `T_sp`, and `Speed_sp` | Canonical names are `Q_feed`, `P_heat`, and `V_line`; no alias map is defined | Define aliases or use only canonical symbols. |
| CSV variables | Requests additional `Q1`, `Q2`, `T`, `P`, and `Speed` columns | Prohibits variables beyond the canonical specification | Define an explicit canonical-to-export alias map, or omit these columns. |
| Phases | Mentions an internal `transition_start` and `completed` sequence | Exported specification permits only `steady_state`, `ramp`, `transient`, `stabilization`, `recovery`, and `fault` state mode | Define whether internal-only phases may exist and their exported representation. |

## Minimum required specification amendment

To unblock implementation without violating the no-invention requirement, amend `simulator_spec.md` with:

- A calibrated numerical parameter table for every symbolic model term, including units and `[Eng]` or `[Design]` provenance.
- An unambiguous discretization rule and a mapping from every response-time range to the selected time constant and dead time.
- Definitions for the disturbance innovations, fault/recovery behavior, action-selection behavior, and outcome-label transitions.
- A risk-score equation, including all inputs, weights, clamping, and historical-precedent rule (or an explicit instruction to omit risk score).
- One reconciled dataset plan: duration, sampling interval, row count, transition count, and intervention frequency.
- One canonical output schema, including any required aliases.

After those changes, implementation can proceed with the requested modular classes while preserving traceability to the amended specification.
