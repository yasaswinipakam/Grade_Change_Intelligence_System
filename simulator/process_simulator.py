"""Forward-Euler process physics specified in simulator_spec.md."""
from __future__ import annotations
from collections import deque
import numpy as np
from .config import CONTROL_KEYS, PARAMS, PHASE_POINTS, RANGES, RECIPES, TOLERANCES

class ProcessSimulator:
    def __init__(self, grade: str, seed: int = 42):
        self.rng = np.random.default_rng(seed); self.grade = grade; self.phase = "steady_state"; self.time = 0
        self.setpoints = RECIPES[grade].copy(); self.state = {**self.setpoints, "D_supply": 1., "D_act": 1., "A_sensor": 1.}
        self.history = {key: deque([self.setpoints.get(key, self.state.get(key, 0.))] * 3, maxlen=3) for key in self.setpoints}
        self.action = None; self.action_magnitude = 0.; self.fault_type = "none"; self.fault_remaining = 0; self.off_spec_duration = 0
        # [Design] warm-up uses the calibrated 500-step requirement from the specification.
        for _ in range(PARAMS["warmup_steps"]): self.step(self.setpoints, process_phase="steady_state", record_noise=False)

    def set_process_phase(self, phase: str) -> None:
        if phase not in PHASE_POINTS: raise ValueError(f"invalid process phase: {phase}")
        self.phase = phase

    def apply_noise(self, magnitude: float, noise_type: str) -> None:
        if noise_type == "external_shock": self.state["D_supply"] = np.clip(self.state["D_supply"] * (1 + magnitude), *RANGES["D_supply"])
        elif noise_type == "process_noise": self.state["D_supply"] = np.clip(self.state["D_supply"] + self.rng.normal(0, magnitude), *RANGES["D_supply"])

    def apply_operator_action(self, action_type: str, magnitude: float) -> None:
        mapping = {"flow_increase": "Q_feed", "flow_decrease": "Q_feed", "pressure_increase": "P_heat", "pressure_decrease": "P_heat", "speed_adjustment": "V_line"}
        key = mapping[action_type]; signed = magnitude if "increase" in action_type else -magnitude
        if action_type == "speed_adjustment": signed = magnitude
        self.setpoints[key] = float(np.clip(self.setpoints[key] * (1 + signed), *RANGES[key])); self.action, self.action_magnitude = action_type, signed * 100

    def _delayed(self, key: str, delay: int) -> float: return list(self.history[key])[-delay-1]
    def _clamp(self, key: str, value: float) -> float: return float(np.clip(value, *RANGES[key]))

    def step(self, setpoints: dict[str, float] | None = None, dt: float = 1., process_phase: str = "steady_state", record_noise: bool = True) -> dict:
        self.set_process_phase(process_phase); self.setpoints.update(setpoints or {})
        p, s, sp = PARAMS, self.state, self.setpoints; d = p["delay_weight"]
        q, c, v, r, f = (self._delayed(k, d) for k in ("Q_feed", "C_feed", "V_line", "R_aid", "F_inert"))
        # Actuator health directly reduces delivered feed; supply quality remains a logged latent disturbance.
        effective_q = q * s["D_act"]
        w_eff = sp["W"] + p["gain_flow"]*(effective_q-sp["Q_feed"])+p["gain_concentration"]*(c-sp["C_feed"])+p["gain_speed"]*(v-sp["V_line"])+p["gain_retention"]*(r-sp["R_aid"])-p["gain_inert"]*(f-sp["F_inert"])
        dm = p["delay_moisture"]; q, v, qa, ph, pa, ex = (self._delayed(k, dm) for k in ("Q_feed","V_line","Q_add","P_heat","P_aux","E_extract"))
        m_eff = sp["M"] + p["gain_flow_m"]*(q-sp["Q_feed"])+p["gain_speed_m"]*(v-sp["V_line"])+p["gain_add"]*(qa-sp["Q_add"])-p["gain_heat"]*(ph-sp["P_heat"])-p["gain_aux"]*(pa-sp["P_aux"])-p["gain_extract"]*(ex-sp["E_extract"])
        h_eff = sp["H"] + p["gain_weight_h"]*(s["W"]-sp["W"])+p["gain_moisture_h"]*(s["M"]-sp["M"])-p["gain_finish_h"]*(s["T_prod"]-sp["T_prod"])
        t_eff = sp["T_prod"] + p["gain_heat_t"]*(ph-sp["P_heat"])+p["gain_aux_t"]*(pa-sp["P_aux"])-p["gain_speed_t"]*(v-sp["V_line"])
        # [Design] Forward Euler, using only calibrated spec parameters.
        for key, eff, tau in (("W",w_eff,p["tau_weight"]),("M",m_eff,p["tau_moisture"]),("H",h_eff,p["tau_thickness"]),("T_prod",t_eff,p["tau_temperature"])): s[key] = self._clamp(key, s[key] + dt*(eff-s[key])/tau)
        for key in CONTROL_KEYS: s[key] = self._clamp(key, sp[key])
        if self.rng.random() < .005: self.apply_noise(self.rng.uniform(-.05,.05), "external_shock")
        if self.rng.random() < .0005: self.fault_type, self.fault_remaining, s["D_act"] = "actuator_loss", int(self.rng.integers(10,31)), self.rng.uniform(.75,.90)
        if self.fault_remaining:
            self.fault_remaining -= 1
        else:
            # [Eng] specified ten-minute exponential recovery after fault duration ends.
            s["D_act"] += (1-s["D_act"])/10
        s["D_supply"] = self._clamp("D_supply", s["D_supply"] + self.rng.normal(0,.01))
        s["A_sensor"] = 0. if self.rng.random() < .01 else 1.
        for key in self.history: self.history[key].append(s[key])
        self.time += 1
        record = self.get_state(record_noise)
        # An operator action is an event, not a sticky state label.
        self.action, self.action_magnitude = None, 0.
        return record

    def get_state(self, record_noise: bool = True) -> dict:
        s = self.state.copy(); target, tol = RECIPES[self.grade], TOLERANCES[self.grade]
        for key, pct in (("Q_feed",.01),("C_feed",.02),("V_line",.01),("P_heat",.01),("P_aux",.01),("Q_add",.02),("E_extract",.01),("R_aid",.02),("F_inert",.02),("W",.005),("M",.01),("H",.01),("T_prod",.01)):
            s[f"observed_{key}"] = s[key] if not record_noise else self._clamp(key, s[key] + self.rng.normal(0, pct*max(abs(s[key]), 1)))
        dev = {k: 100*(s[k]-target[k])/target[k] for k in ("W","M","H")}; off = any(abs(s[k]-target[k]) > tol[k] for k in tol)
        self.off_spec_duration = self.off_spec_duration + 1 if off else 0
        risk = 8*abs(dev["W"])+5*abs(dev["M"])+3*abs(dev["H"])+PHASE_POINTS[self.phase]+min(20,2*self.off_spec_duration)+(10 if self.fault_remaining else 0)
        return {**s, "grade": self.grade, "process_phase": self.phase, "basis_weight_deviation": dev["W"], "risk_score": float(np.clip(risk,0,100)), "off_spec": off, "off_spec_duration_minutes": self.off_spec_duration, "operator_action": self.action or "none", "operator_action_magnitude": self.action_magnitude, "fault_type": self.fault_type, "fault_active": bool(self.fault_remaining)}
