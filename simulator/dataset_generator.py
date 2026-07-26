"""Batch orchestration with dense transition rows and sparse steady-state rows."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import numpy as np
from .config import RECIPES
from .process_simulator import ProcessSimulator
from .transition_scheduler import TransitionScheduler
from .validation_engine import ValidationEngine
class DatasetGenerator:
    def __init__(self, seed=42): self.seed=seed; self.rng=np.random.default_rng(seed); self.validator=ValidationEngine()
    def generate_dataset(self, num_transitions=90):
        sim=ProcessSimulator("Grade A", self.seed); scheduler=TransitionScheduler(sim,self.rng); rows=[]; outcomes=[]; timestamp=datetime(2026,1,1,tzinfo=timezone.utc)
        def add(row, minutes=1):
            nonlocal timestamp
            row={"timestamp":timestamp.isoformat(), **row, "successful_transition": False, "transition_id": "", "source_grade": "", "destination_grade": "", "planned_duration_minutes": 0, "ramp_progress": 0.}; rows.append(row); timestamp += timedelta(minutes=minutes)
        grades=list(RECIPES)
        for index in range(num_transitions):
            # [Design] sparse steady-state export every 5 min; simulate every minute.
            excitation_factors={}; excitation_remaining=0
            for minute in range(int(self.rng.integers(120,301))):
                sp=RECIPES[sim.grade].copy()
                # [Design] specification-authorized persistent ±8% independent excitation.
                if excitation_remaining == 0:
                    keys=("Q_feed","C_feed","V_line","P_heat","P_aux","Q_add","E_extract","R_aid","F_inert")
                    excitation_factors={key: float(self.rng.uniform(-.08,.08)) for key in keys}; excitation_remaining=10
                for key, factor in excitation_factors.items(): sp[key] *= 1 + factor
                excitation_remaining -= 1
                row=sim.step(sp, process_phase="steady_state")
                if minute % 5 == 0: add(row, 5)
            choices=[g for g in grades if g != sim.grade]; plan=scheduler.plan_transition(sim.grade, choices[int(self.rng.integers(len(choices)))], index+1)
            transition, outcome=scheduler.execute_transition(plan); valid,_=self.validator.validate_transition(transition)
            if valid:
                for row in transition: add(row); rows[-1]["successful_transition"]=(outcome=="success")
                outcomes.append(outcome)
            if (index+1) % 100 == 0: print(f"Generated {index+1}/{num_transitions} transitions")
        # [Design] balance final compact export across grades instead of filling from the final grade.
        quota=10000
        counts={grade:sum(row["grade"] == grade for row in rows) for grade in grades}
        for grade in grades:
            sim.grade, sim.setpoints = grade, RECIPES[grade].copy()
            sim.state.update({key: RECIPES[grade][key] for key in ("W","M","H","T_prod")})
            while counts[grade] < quota:
                for _ in range(5): sim.step(RECIPES[grade], process_phase="steady_state")
                add(sim.get_state(), 5); counts[grade] += 1
        balanced=[]; used={grade:0 for grade in grades}
        for row in rows:
            if used[row["grade"]] < quota: balanced.append(row); used[row["grade"]] += 1
        return balanced, outcomes
