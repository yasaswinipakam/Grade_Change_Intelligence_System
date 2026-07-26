"""Online and batch validation against the shared specification limits."""
from __future__ import annotations
import math
import numpy as np
from .config import RANGES
class ValidationEngine:
    def validate_state(self, state):
        bad = [k for k, (lo, hi) in RANGES.items() if k in state and (not math.isfinite(float(state[k])) or not lo <= float(state[k]) <= hi)]
        return not bad, bad
    def validate_transition(self, rows):
        phases = [r["process_phase"] for r in rows]; valid = {"ramp","transient","stabilization","recovery"}
        bad = [] if all(p in valid for p in phases) else ["invalid phase"]
        for row in rows:
            ok, reasons = self.validate_state(row)
            if not ok: bad.extend(reasons)
        return not bad, sorted(set(bad))
    def validate_dataset(self, rows, outcomes):
        success = 100*sum(o == "success" for o in outcomes)/max(1,len(outcomes)); numeric = [v for r in rows for v in r.values() if isinstance(v,(int,float,np.number))]
        return {"records":len(rows),"transitions":len(outcomes),"success_rate":success,"all_finite":bool(np.isfinite(numeric).all()),"phase_counts":{p:sum(r["process_phase"]==p for r in rows) for p in ("steady_state","ramp","transient","stabilization","recovery")},"warnings": [] if 70 <= success <= 90 else ["success rate outside 70-90% specification band"]}
