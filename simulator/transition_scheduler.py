"""Transition planning and execution; physics remains in ProcessSimulator."""
from __future__ import annotations
from .config import CONTROL_KEYS, RECIPES, TOLERANCES
class TransitionScheduler:
    def __init__(self, simulator, rng): self.simulator, self.rng = simulator, rng
    def plan_transition(self, from_grade, to_grade, transition_id):
        return {"id":transition_id,"from_grade":from_grade,"to_grade":to_grade,"duration":int(self.rng.integers(10,23)),"action":self.rng.random()<.20,"fault":self.rng.random()>=.78}
    def execute_transition(self, plan):
        sim, source, target = self.simulator, RECIPES[plan["from_grade"]], RECIPES[plan["to_grade"]]; rows=[]; action_done=False
        for minute in range(plan["duration"]):
            fraction=(minute+1)/plan["duration"]; sp={k:source[k]+fraction*(target[k]-source[k]) for k in CONTROL_KEYS}
            # Recipe-relative quality targets change with the destination grade during the ramp.
            sp.update({k:target[k] for k in ("W","M","H","T_prod")})
            row=sim.step(sp, process_phase="ramp"); row.update(transition_id=plan["id"], source_grade=plan["from_grade"], destination_grade=plan["to_grade"], planned_duration_minutes=plan["duration"], ramp_progress=fraction); rows.append(row)
        sim.grade=plan["to_grade"]
        for minute in range(10):
            phase="transient" if minute < 3 else "stabilization"
            if plan["fault"] and minute == 0:
                # [Eng] calibrated actuator-loss magnitude and duration from the specification.
                sim.fault_type, sim.fault_remaining, sim.state["D_act"] = "actuator_loss", 30, .75
            if plan["action"] and not action_done and minute == 2:
                deficit=sim.state["W"] < target["W"]; sim.apply_operator_action("flow_increase" if deficit else "pressure_increase", self.rng.uniform(.02,.08)); action_done=True
            row=sim.step(RECIPES[plan["to_grade"]], process_phase=phase); row.update(transition_id=plan["id"], source_grade=plan["from_grade"], destination_grade=plan["to_grade"], planned_duration_minutes=plan["duration"], ramp_progress=1.); rows.append(row)
        success=self._in_recipe(rows[-1]); outcome="success" if success else "recovery"
        if outcome=="recovery":
            for _ in range(5):
                row=sim.step(RECIPES[plan["to_grade"]], process_phase="recovery"); row.update(transition_id=plan["id"], source_grade=plan["from_grade"], destination_grade=plan["to_grade"], planned_duration_minutes=plan["duration"], ramp_progress=1.); rows.append(row)
            outcome="success" if self._in_recipe(rows[-1]) else "failure"
        if outcome == "failure":
            # [Design] reset after the labeled failed episode so it cannot poison later steady data.
            sim.fault_remaining, sim.fault_type, sim.state["D_act"], sim.off_spec_duration = 0, "none", 1., 0
        return rows, outcome
    def _in_recipe(self, state):
        recipe,tol=RECIPES[self.simulator.grade],TOLERANCES[self.simulator.grade]
        return all(abs(state[k]-recipe[k]) <= tol[k] for k in tol)
