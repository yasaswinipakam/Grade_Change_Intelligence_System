# Physics-Inspired Process Simulator Specification

## Purpose, scope, and provenance rule

This is the implementation contract for a synthetic-data simulator of a generic continuous manufacturing line. It emits sampled process state, quality outcomes, transition events, disturbances, interventions, constraint outcomes, and labels for deviation-prediction and recommendation models.

Every simulator number has a provenance tag:

- **[Lit]** Literature-Supported: reported in [deep-research-report.md](deep-research-report.md), with the report passage named.
- **[Eng]** Engineering Assumption: a non-literature estimate and its reason are stated.
- **[Design]** Derived Design Choice: chosen for reproducible architecture or dataset utility and justified.

Citation years are bibliographic metadata rather than simulator settings. The supplied research report does not contain page-level excerpts for most primary papers. This document therefore cites the exact report passage and never invents a paper quote or page. A plant-use revision must replace report citations with verified primary-source pages.

Each output row contains latent and observed values, active grade, mode (`steady`, `transition`, `recovery`, or `fault`), all setpoints, action and fault identifiers, constraint status, and run seed. An operator action is always a discrete and logged setpoint adjustment.

## Process variables

All numbers in this table are independently tagged. **[Lit]** ranges are quoted or summarized in the named report passage; **[Eng]** ranges are generic simulator envelopes, not plant ratings. All setpoints are **[Design]** centers selected inside the envelope to make recipes separable.

| Variable | Symbol | Units | Range | Range source | Nominal setpoint | Setpoint source | Meaning |
|---|---|---|---|---|---|---|---|
| Primary material flow | `Q_feed` | L/min | `50–200` **[Lit]** | Report “Synthetic Dataset Design” lists `50–200 L/min`. | `140` **[Design]** | Middle recipe reference. | Main material-feed rate. |
| Feed concentration | `C_feed` | % | `0.5–1.5` **[Lit]** | Report “Process Variables”: printing-grade consistency is “around `0.5–1.5%`.” | `1.0` **[Design]** | Center of range. | Active-material fraction. |
| Line speed | `V_line` | m/min | `100–2000` **[Lit]** | Report “Synthetic Dataset Design” lists `100–2000 m/min`. | `900` **[Design]** | Mid-operating reference. | Throughput speed. |
| Primary heating pressure | `P_heat` | bar | `1–10` **[Lit]** | Report “Synthetic Dataset Design” lists `1–10 bar`. | `7` **[Design]** | Leaves control headroom. | Main thermal energy. |
| Auxiliary heating pressure | `P_aux` | bar | `0–8` **[Eng]** | Needed as a bounded secondary thermal actuator. | `4` **[Design]** | Mid-envelope reference. | Upstream heat/dewatering energy. |
| Dilution/recycle flow | `Q_recycle` | L/min | `0–100` **[Eng]** | Generic bounded dilution path. | `35` **[Design]** | Allows corrective authority. | Alters effective feed solids/load. |
| Added-moisture flow | `Q_add` | kg/h | `0–80` **[Eng]** | Explicit bounded moisture-addition actuator. | `15` **[Design]** | Stable-operation reference. | Direct liquid addition. |
| Extraction intensity | `E_extract` | kPa | `50–90` **[Lit]** | Report “Synthetic Dataset Design” lists `50–90 kPa` press vacuum. | `70` **[Design]** | Center of range. | Mechanical moisture removal. |
| Retention/yield aid | `R_aid` | L/min | `0–12` **[Eng]** | Report names the pathway but no numeric range. | `4` **[Design]** | Nonzero observable effect. | Additive affecting retained material. |
| Inert-additive flow | `F_inert` | kg/h | `0–60` **[Eng]** | Generic bounded composition actuator. | `20` **[Design]** | Moderate loading. | Non-active composition fraction. |
| Primary quality weight | `W` | g/m² | `30–300` **[Lit]** | Report states low grades `30–50 g/m²`, high grades `300+ g/m²`; conservative inclusive envelope. | `120` **[Design]** | Middle recipe target. | Mass per unit area. |
| Final moisture | `M` | % | `4–10` **[Lit]** | Report “Process Variables” gives final target `4–10%`. | `6` **[Design]** | Center of range. | Residual moisture. |
| Product thickness | `H` | µm | `70–300` **[Lit]** | Report gives `70–300 µm` examples. | `150` **[Design]** | Middle recipe reference. | Final thickness/caliper. |
| Product temperature | `T_prod` | °C | `20–140` **[Eng]** | Generic safe thermal observation window. | `85` **[Design]** | Thermal-state reference. | Exit thermal condition. |
| Supply-quality factor | `D_supply` | fraction | `0.80–1.20` **[Eng]** | Bounded multiplicative supply disturbance. | `1.00` **[Design]** | Neutral supply. | Latent feed-quality modifier. |
| Actuator-health factor | `D_act` | fraction | `0.75–1.00` **[Eng]** | Bounded partial-loss representation. | `1.00` **[Design]** | Healthy state. | Actuator effectiveness. |
| Sensor availability | `A_sensor` | fraction | `0–1` **[Eng]** | Valid/invalid observation state. | `1` **[Design]** | Fully available sensor. | Observation validity. |

## Causal relationships

The table is the simulator’s mandatory directional contract. The named excerpts are from the research report, which cites Chu et al. **[Lit—bibliographic year]**, Shen et al. **[Lit—bibliographic year]**, and related sources. Strength means direct primary pathway (**strong**), documented coupled pathway (**moderate**), or explicitly small pathway (**weak**).

| Cause → effect | Direction | Mechanism | Literature evidence | Strength and behavior |
|---|---|---|---|---|
| `Q_feed → W` | `↑ → ↑` | More active material deposited per time. | Report “Causal Relationships”: “Stock Flow ↑ → Basis Weight ↑.” | Strong **[Lit]**; positive with transport lag. |
| `C_feed → W` | `↑ → ↑` | More active solids at fixed flow. | “Headbox Consistency ↑ → Basis Weight ↑.” | Strong **[Lit]**; positive; interacts with `Q_feed`. |
| `V_line → W` | `↑ → ↓` | Material distributed across more product length. | “Machine Speed ↑ → Basis Weight ↓.” | Strong **[Lit]**; inverse monotonic. |
| `Q_feed → M` | `↑ → ↑` | Higher incoming water/material load. | “Stock Flow ↑ → … Moisture ↑.” | Moderate **[Lit]**; lagged and thermal-coupled. |
| `V_line → M` | `↑ → ↑` | Less drying residence time. | “Machine Speed ↑ → … Moisture ↑.” | Moderate **[Lit]**; lagged. |
| `P_heat → M` | `↑ → ↓` | More thermal removal/evaporation. | “Dryer Steam Pressure ↑ → Paper Moisture ↓.” | Strong **[Lit]**; nonlinear saturation. |
| `P_aux → M` | `↑ → ↓` | Improved upstream dewatering. | “Steam Box Pressure ↑ → Web Moisture ↓.” | Moderate **[Lit]**; lagged negative. |
| `Q_add → M` | `↑ → ↑` | Direct moisture addition. | “Water Spray Flow ↑ → Web Moisture ↑.” | Strong **[Lit]**; positive with transport lag. |
| `E_extract → M` | `↑ → ↓` | More mechanical water removal. | “Press Load/Vacuum ↑ → Web Moisture ↓.” | Moderate **[Lit]**; saturating near dry limit. |
| `R_aid → W` | `↑ → ↑` | Higher retention leaves more material in product. | “Retention Aid Dose ↑ → Retention ↑ → Basis Weight ↑.” | Moderate **[Lit]**; slow mixed response. |
| `F_inert → W` | `↑ → ↓` | Inert fraction dilutes active material. | “Filler … ↑ → slight ↓ Basis Weight.” | Weak **[Lit]**; must not dominate flow. |
| `W → H` | `↑ → ↑` | More mass produces thicker product. | “Basis Weight ↑ → Caliper ↑.” | Strong **[Lit]**; positive coupled output. |
| `M → H` | `↑ → ↑` | Moisture participates in thickness outcome. | Report says moisture and weight jointly determine caliper. | Moderate **[Eng]** local sign; calibrate before plant use. |

## Time dynamics

Response time means time to approximately sixty-three percent of final step change. The report gives indicative lags, not fitted model parameters. Orders are implementation abstractions and all settling times are assumptions.

| Output | Dominant inputs | Response time | Source | Dynamic order/justification | Settling time | Source |
|---|---|---|---|---|---|---|
| `W` | `Q_feed`, `C_feed`, `V_line`, `R_aid` | `1–2 min` **[Lit]** | Report “Physics-Inspired Simulator Design”: basis-weight change “may have a `1–2 min` delay.” | First-order-plus-dead-time **[Design]**; represents transport and dominant monotonic response. | `4–8 min` **[Eng]** | Multiple response windows for a stable loop. |
| `M` | `P_heat`, `P_aux`, `Q_add`, `E_extract`, `V_line` | `3–5 min` **[Lit]** | Report states moisture takes `3–5 min` for full dryer effect. | First-order-plus-dead-time with saturation **[Design]**; report calls drying slower/nonlinear. | `10–16 min` **[Eng]** | Allows thermal recovery within a transition. |
| `H` | `W`, `M`, `T_prod` | `2–4 min` **[Eng]** | Assumed short finishing lag. | Coupled first-order **[Design]**; avoids unsupported independent finishing model. | `8–12 min` **[Eng]** | Follows mass and moisture convergence. |
| `T_prod` | `P_heat`, `P_aux`, `V_line` | `1–3 min` **[Eng]** | Assumed faster upstream thermal state. | First-order-plus-dead-time **[Design]**. | `4–10 min` **[Eng]** | Faster than moisture. |
| `R_aid` effect | `R_aid`, `D_supply` | `5–10 min` **[Eng]** | Mixing/residence-time assumption. | First-order **[Design]**. | `15–25 min` **[Eng]** | Prevents instant additive effect. |

## Grade recipes

Grade names are generic. Every target and tolerance is **[Design]**: selected inside the process-variable envelopes to generate three separable products, not to represent published product specifications.

| Grade | Primary `W` target and window | Secondary `M` target and window | Tertiary `H` target and window | Rationale |
|---|---|---|---|---|
| Grade A — Light | `60`; `57–63 g/m²` **[Design]** | `5`; `4–6 %` **[Design]** | `90`; `81–99 µm` **[Design]** | Lower-region product within literature-informed envelopes. |
| Grade B — Standard | `120`; `114–126 g/m²` **[Design]** | `6`; `5–7 %` **[Design]** | `150`; `135–165 µm` **[Design]** | Mid-envelope reference product. |
| Grade C — Heavy | `220`; `209–231 g/m²` **[Design]** | `7`; `6–8 %` **[Design]** | `240`; `216–264 µm` **[Design]** | Upper-region product with hard-limit margin. |

All recipe setpoints below are **[Design]**, derived from the canonical variable envelopes to create distinguishable operating conditions. `D_supply`, `D_act`, and `A_sensor` remain at their canonical nominal values for all healthy, steady recipes.

| Variable | Grade A | Grade B | Grade C |
|---|---:|---:|---:|
| `Q_feed` L/min | `85` **[Design]** | `140` **[Design]** | `180` **[Design]** |
| `C_feed` % | `0.7` **[Design]** | `1.0` **[Design]** | `1.3` **[Design]** |
| `V_line` m/min | `1000` **[Design]** | `900` **[Design]** | `750` **[Design]** |
| `P_heat` bar | `6` **[Design]** | `7` **[Design]** | `8` **[Design]** |
| `P_aux` bar | `3` **[Design]** | `4` **[Design]** | `5` **[Design]** |
| `Q_recycle` L/min | `45` **[Design]** | `35` **[Design]** | `25` **[Design]** |
| `Q_add` kg/h | `10` **[Design]** | `15` **[Design]** | `20` **[Design]** |
| `E_extract` kPa | `75` **[Design]** | `70` **[Design]** | `65` **[Design]** |
| `R_aid` L/min | `3` **[Design]** | `4` **[Design]** | `6` **[Design]** |
| `F_inert` kg/h | `15` **[Design]** | `20` **[Design]** | `25` **[Design]** |
| `T_prod` °C | `75` **[Design]** | `85` **[Design]** | `95` **[Design]** |

## Transition scenarios

Transition duration is sampled in `10–22 min` **[Lit]**. Report “Grade Change Analysis” attributes approximately `22 min` manual and approximately `10 min` model-predictive transitions to Chu et al. **[Lit—bibliographic year]**. The default is `15 min` **[Design]**, deliberately between those endpoints.

Setpoints use coordinated piecewise-linear ramps **[Design]** for `Q_feed`, `C_feed`, `V_line`, `P_heat`, `P_aux`, and `E_extract`. The report allows linear or MPC-like synthetic trajectories; linear ramps are selected because they are auditable. Latent outputs retain the declared delays and never teleport to a new recipe.

An operator intervention changes one setpoint by `2–8 %` **[Design]**: increase/decrease feed, speed, either pressure, added moisture, or hold. These action types are **[Lit]** in kind because the report identifies flow, steam/pressure, and speed as grade-change controls. `25 %` **[Design]** of transitions receive at least one intervention, after `3 min` **[Design]** of elapsed transition; this creates corrective-action examples without making manual action dominant. Success means `W`, `M`, and `H` all enter the destination windows by planned end. Batch success must be `70–90 %` **[Lit]**, per the supplied research foundation.

## Constraints

### Hard limits

Hard limits are exactly the variable-table envelopes; each retains its **[Lit]** or **[Eng]** classification there. A proposed action outside a hard limit is rejected and logged as `hard_fail`.

### Recipe limits and safety margin

The Grade A/B/C windows are the recipe limits and are **[Design]**. A state outside them but inside hard limits is feasible but labeled `recipe_fail`. Weight may overshoot by `3 %` of active target for at most `2 min` **[Design]**; this separates transient lag from sustained off-spec operation. Moisture and thickness receive no additional allowance **[Design]**, making slow thermal excursions visible to learning models.

## Dynamics modeling

The equations below define the physics structure. Their executable numerical values are supplied exactly once in the authoritative **Implementation Parameter Table** that follows. A numeric value marked **[Eng]** is an explicit calibration assumption, not literature evidence. Forward Euler is the authorized discretization **[Design]** because the one-minute integration step is small relative to the declared response constants.

### Weight

`dW/dt = (W_effective - W) / tau_weight + epsilon_weight`

`W_effective = W_sp + gain_flow × (Q_feed_delay - Q_feed_sp) + gain_concentration × (C_feed_delay - C_feed_sp) + gain_speed × (V_line_delay - V_line_sp) + gain_retention × (R_aid_delay - R_aid_sp) - gain_inert × (F_inert_delay - F_inert_sp)`

The structure is **[Lit]**-informed by the report’s flow/consistency/speed relationship. Recipe-relative form is **[Design]**: it preserves documented causal directions while anchoring each grade at its declared target.

### Moisture

`dM/dt = (M_effective - M) / tau_moisture + epsilon_moisture`

`M_effective = M_sp + gain_flow_m × (Q_feed_delay - Q_feed_sp) + gain_speed_m × (V_line_delay - V_line_sp) + gain_add × (Q_add_delay - Q_add_sp) - gain_heat × (P_heat_delay - P_heat_sp) - gain_aux × (P_aux_delay - P_aux_sp) - gain_extract × (E_extract_delay - E_extract_sp)`

The signs implement the literature-grounded relationships above. Saturating final state at hard limits is **[Design]**.

### Thickness and temperature

`dH/dt = (H_sp + gain_weight_h × (W_delay - W_sp) + gain_moisture_h × (M_delay - M_sp) - gain_finish_h × (T_prod_delay - T_prod_sp) - H) / tau_thickness + epsilon_thickness`

`dT_prod/dt = (T_prod_sp + gain_heat_t × (P_heat_delay - P_heat_sp) + gain_aux_t × (P_aux_delay - P_aux_sp) - gain_speed_t × (V_line_delay - V_line_sp) - T_prod) / tau_temperature + epsilon_temperature`

The weight pathway is **[Lit]**-informed; moisture/finishing local signs and the intermediate-temperature representation are **[Eng]** and **[Design]** respectively.

### Disturbance and health states

`D_supply_next = clamp(D_supply + eta_supply, supply_min, supply_max)`

`D_act_next = clamp(D_act + eta_actuator, actuator_min, actuator_max)`

Bounds are the variable-table **[Eng]** limits; `clamp` is **[Design]** to preserve valid latent state. Faults override `D_act` or `A_sensor` and must carry a fault label.

## Noise and disturbances

All following values are **[Eng]**, except where marked **[Design]**. They are realistic-data choices, not claimed sensor specifications.

| Item | Magnitude | Source and rationale |
|---|---|---|
| Flow and pressure observation noise | `±1 %` Gaussian **[Eng]** | Modest analogue variation; keeps actions identifiable. |
| Concentration/additive noise | `±2 %` Gaussian **[Eng]** | Assumed mixing/dosing uncertainty. |
| Weight noise | `±0.5 %` Gaussian **[Eng]** | Preserves small useful deviation examples. |
| Moisture, thickness, temperature noise | `±1 %` Gaussian **[Eng]** | Keeps thermal response observable. |
| Supply disturbance | `±5 %` step **[Design]** | Creates corrective-action learning cases. |
| Actuator effectiveness loss | `10–25 %` **[Eng]** | Partial, recoverable degradation. |
| Sensor dropout | `1 %` of samples **[Design]** | Explicit small missing-data class. |

## Dataset plan and transition frequency

Sample every `1 min` **[Design]**. This resolves the `1–2 min` weight delay and `3–5 min` moisture response **[Lit]** while avoiding repeated rows. Run for `90 days` **[Design]**, producing `129,600` rows **[Design]** from `90 × 24 × 60`; the duration provides repeated recipes and recoveries without excessive size. Schedule `60–120` transitions **[Design]**, using a non-uniform Poisson-like arrival process **[Design]** and a no-overlap rule. This is dataset coverage, not a claim about plant scheduling. Keep aggregate successful transitions within `70–90 %` **[Lit]**.

## Simplifications register

| Simplification | Reason | Expected impact | Affects qualitative behavior? |
|---|---|---|---|
| First-order-plus-dead-time quality models **[Design]** | Transparent calibration of reported lag. | Misses oscillatory/multi-stage response. | No; directions and delays remain. |
| Local linear gains **[Design]** | Stable synthetic labels. | Lower fidelity at extremes. | No; monotonic behavior remains. |
| Four dynamic product outputs **[Design]** | Limits scope to stated targets. | Omits profile/mechanical phenomena. | No for declared labels. |
| Simplified additive pathways **[Eng]** | Report gives direction, not generic full model. | Secondary effects may be inaccurate. | No; effects remain secondary. |
| Independent Gaussian noise **[Design]** | Repeatable baseline testing. | Omits coloured drift. | No; latent trends remain. |
| No aging beyond `D_act` **[Design]** | Compact state space. | Long-term fouling absent. | No for selected horizon. |
| No spatial profile model **[Design]** | Line-average decision scope. | No cross-direction variation. | No for line-average labels. |

## Validation criteria

| Check | Pass condition | Fail condition | Basis |
|---|---|---|---|
| Directionality | Required signs in causal table remain after conditioning by grade/mode. | Any required sign reverses. | **[Lit]** causal contract. |
| Weight delay | Median is `1–2 min`. | Outside interval. | **[Lit]** report “Physics-Inspired Simulator Design.” |
| Moisture response | Full response is `3–5 min`. | Outside interval. | **[Lit]** same report passage. |
| Transition time | Every nominal transition is `10–22 min`; default is `15 min`. | Outside range. | **[Lit]** endpoints; **[Design]** default. |
| Success rate | Batch aggregate is `70–90 %`. | Below `70 %` or above `90 %`. | **[Lit]** task research foundation. |
| Constraint integrity | `100 %` of unlabeled-fault latent states satisfy hard limits. | Any unlabelled violation. | **[Design]** traceability rule. |
| Label/action audit | `100 %` reproducible recipe labels and action before/after records. | Missing or irreproducible record. | **[Design]** training-data integrity. |

## Research record

The authoritative evidence source is [deep-research-report.md](deep-research-report.md): its sections “Process Variables,” “Causal Relationships,” “Grade Change Analysis,” “Physics-Inspired Simulator Design,” and “Synthetic Dataset Design” support the **[Lit]** entries. Its bibliography names Chu et al., Shen et al., Murphy and Starr, and Callicott. Page-verified primary-source citations are a required future evidence-review deliverable before use beyond synthetic ML development.

## Implementation Parameter Table — authoritative calibration

This table is the sole numerical authority for executable dynamics. It resolves every symbol used in the equations above. Values are engineering calibrations chosen to preserve the literature-supported directions and the documented response windows; they are not reported plant coefficients.

| Parameter | Value | Units | Classification | Used in | Calibration rationale |
|---|---:|---|---|---|---|
| `dt` | `1` | min | **[Design]** | all Euler updates | Canonical integration interval. |
| `tau_weight` | `1.5` | min | **[Eng]** | weight | Gives a fast response after the declared `1 min` weight delay. |
| `delay_weight` | `1` | min | **[Lit]** | weight inputs | Inside the report’s `1–2 min` basis-weight delay. |
| `gain_flow` | `0.25` | g/m² per L/min | **[Eng]** | weight | Flow changes visibly alter weight without overwhelming grade targets. |
| `gain_concentration` | `50` | g/m² per % | **[Eng]** | weight | A concentration change has a strong, documented effect. |
| `gain_speed` | `-0.03` | g/m² per m/min | **[Eng]** | weight | Preserves inverse speed-to-weight direction. |
| `gain_retention` | `1` | g/m² per L/min | **[Eng]** | weight | Retention is secondary to feed flow. |
| `gain_inert` | `0.10` | g/m² per kg/h | **[Eng]** | weight | Implements the report’s slight negative inert-additive effect. |
| `tau_moisture` | `4` | min | **[Eng]** | moisture | Matches the documented `3–5 min` thermal response scale. |
| `delay_moisture` | `1` | min | **[Eng]** | moisture inputs | Adds transport effect while keeping `63%` response within the documented window. |
| `gain_flow_m` | `0.01` | % per L/min | **[Eng]** | moisture | Positive flow-to-moisture coupling. |
| `gain_speed_m` | `0.003` | % per m/min | **[Eng]** | moisture | Positive speed-to-moisture coupling, weaker than thermal control. |
| `gain_add` | `0.02` | % per kg/h | **[Eng]** | moisture | Direct added-moisture effect. |
| `gain_heat` | `0.12` | % per bar | **[Eng]** | moisture | Strong negative heating effect. |
| `gain_aux` | `0.08` | % per bar | **[Eng]** | moisture | Secondary negative heating effect. |
| `gain_extract` | `0.025` | % per kPa | **[Eng]** | moisture | Moderate extraction effect. |
| `tau_thickness` | `3` | min | **[Eng]** | thickness | Inside declared `2–4 min` thickness response. |
| `delay_thickness` | `1` | min | **[Eng]** | thickness inputs | Short finishing delay. |
| `gain_weight_h` | `0.70` | µm per g/m² | **[Eng]** | thickness | Weight is the dominant thickness pathway. |
| `gain_moisture_h` | `2` | µm per % | **[Eng]** | thickness | Moderate local moisture coupling. |
| `gain_finish_h` | `0.20` | µm per °C | **[Eng]** | thickness | Small finishing-temperature reduction. |
| `tau_temperature` | `2` | min | **[Eng]** | temperature | Inside declared `1–3 min` temperature response. |
| `delay_temperature` | `1` | min | **[Eng]** | temperature inputs | Short thermal transport delay. |
| `gain_heat_t` | `2` | °C per bar | **[Eng]** | temperature | Main heating response. |
| `gain_aux_t` | `1` | °C per bar | **[Eng]** | temperature | Auxiliary heating response. |
| `gain_speed_t` | `0.01` | °C per m/min | **[Eng]** | temperature | Faster line lowers product thermal state. |
| `convergence_tolerance` | `0.01` | % change/min | **[Design]** | warm-up/stabilization | Standard deterministic convergence threshold. |
| `warmup_steps` | `500` | integration steps | **[Design]** | initialization | Task-authorized steady-state convergence initialization. |

The simulator uses the Forward Euler update `x_next = x_current + dt × derivative` **[Design]**. It stores delayed inputs in minute-indexed buffers sized from the listed delays. Every target-relative setpoint `*_sp` comes from the active grade recipe table.

## Disturbance, fault, and recovery models

### Supply disturbance

`D_supply_next = clamp(D_supply + eta_supply, 0.80, 1.20)` where `eta_supply ~ Normal(0, 0.01)` **[Eng]** at each one-minute update. A discrete supply shock occurs with probability `0.005` per minute **[Design]**; its multiplier is sampled uniformly from `-5%` to `+5%` **[Design]**, lasts `5–15 min` **[Eng]**, and then linearly returns to neutral over `5 min` **[Eng]**. The bounds preserve the existing **[Eng]** variable envelope.

### Actuator fault and recovery

An actuator fault occurs with probability `0.0005` per minute **[Design]**. On trigger, `D_act` is reduced uniformly by `10–25%` **[Eng]**, lasts `10–30 min` **[Eng]**, then recovers exponentially toward `1.00` with `tau_fault_recovery = 10 min` **[Eng]**. A sensor dropout occurs with probability `1%` per sample **[Design]**, sets `A_sensor = 0` for that record, and publishes the last valid observed value plus the availability flag; latent state remains valid.

### Fault labels and outcomes

Each fault row has `fault_type`, `fault_active`, and `recovery_needed`. A transition is **successful** when `W`, `M`, and `H` enter the destination recipe windows before planned end; **recovered** when an operator action restores all three within an extra `5 min` **[Design]**; otherwise **failed**. A hard-limit attempt is rejected before state update and logged as `hard_fail` **[Design]**.

## Risk-score definition

Risk is deterministic and requires no external historical model. The historical-precedent contribution is explicitly `0` points **[Design]** because this simulator has no prior-history query in its state contract.

`risk_score = clip(8 × abs(dev_weight) + 5 × abs(dev_moisture) + 3 × abs(dev_thickness) + phase_points + min(20, 2 × off_spec_duration) + constraint_points + fault_points, 0, 100)`

Where `dev_weight`, `dev_moisture`, and `dev_thickness` are each percentage deviation from active recipe target. `phase_points` is `0` in steady state, `8` in ramp, `12` in transient, `6` in stabilization, and `15` in recovery **[Design]**. `constraint_points` is `30` for an active hard failure and `0` otherwise **[Design]**. `fault_points` is `10` for an active fault and `0` otherwise **[Design]**. The terms are all **[Design]** weights selected to make quality deviation dominant, while visibly elevating risk during transition, fault, and sustained off-spec conditions. `basis_weight_deviation = (W - W_sp) / W_sp × 100` **[Design]** is the primary ML target.

## Canonical dataset plan

Every later implementation must use this table; it supersedes earlier narrative dataset counts and operator-action frequencies.

| Item | Canonical value | Classification | Rationale |
|---|---:|---|---|
| Simulation duration | `90 days` | **[Design]** | Required three-month horizon. |
| Integration interval | `1 min` | **[Design]** | Resolves documented weight and moisture dynamics. |
| Export policy | all transition/fault/recovery rows at `1 min`; steady rows every `5 min` | **[Design]** | Preserves short dynamics while limiting CSV size. |
| Expected exported rows | approximately `30,000` | **[Design]** | Reconciles required horizon with compact ML artifact. |
| Transition count | `90` | **[Design]** | Fits the compact data plan and provides diverse grade changes. |
| Planned transition duration | `15 min` | **[Design]** | Center of literature-informed range. |
| Allowed transition duration | `10–22 min` | **[Lit]** | Reported grade-change endpoints. |
| Operator-intervention rate | `20%` | **[Design]** | Conservative resolution of earlier `20%`/`25%` ambiguity. |
| Intervention magnitude | `2–8%` | **[Design]** | Existing specification corrective-action band. |
| Success target | `78%` | **[Design]** | Inside literature-informed `70–90%` band. |
| Permitted success band | `70–90%` | **[Lit]** | Task research foundation. |

Within each steady-state recipe, perturb each controllable setpoint independently within `±8%` for `10 min` **[Design]**. This bounded excitation equals the documented maximum corrective-action magnitude but is not an operator action; it exists to make documented causal directions identifiable without leaving hard limits.

## Implementation completeness and self-consistency audit

The calibration table defines every evaluated equation parameter exactly once. No executable symbol remains unresolved: grade setpoints define `*_sp`; the canonical variable table defines clamps; the calibration table defines gains, delays, time constants, warm-up, and convergence; disturbance section defines random processes; risk section defines all weights and clipping; and the dataset plan resolves prior count/frequency ambiguity. A future change must update this specification before changing simulator code.
