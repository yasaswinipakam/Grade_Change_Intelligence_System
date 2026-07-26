"""Single source for values calibrated in simulator_spec.md."""
from __future__ import annotations

RANGES = {
    "Q_feed": (50., 200.), "C_feed": (.5, 1.5), "V_line": (100., 2000.),
    "P_heat": (1., 10.), "P_aux": (0., 8.), "Q_recycle": (0., 100.),
    "Q_add": (0., 80.), "E_extract": (50., 90.), "R_aid": (0., 12.),
    "F_inert": (0., 60.), "W": (30., 300.), "M": (4., 10.),
    "H": (70., 300.), "T_prod": (20., 140.), "D_supply": (.8, 1.2),
    "D_act": (.75, 1.), "A_sensor": (0., 1.),
}
RECIPES = {
    "Grade A": dict(Q_feed=85., C_feed=.7, V_line=1000., P_heat=6., P_aux=3., Q_recycle=45., Q_add=10., E_extract=75., R_aid=3., F_inert=15., W=60., M=5., H=90., T_prod=75.),
    "Grade B": dict(Q_feed=140., C_feed=1., V_line=900., P_heat=7., P_aux=4., Q_recycle=35., Q_add=15., E_extract=70., R_aid=4., F_inert=20., W=120., M=6., H=150., T_prod=85.),
    "Grade C": dict(Q_feed=180., C_feed=1.3, V_line=750., P_heat=8., P_aux=5., Q_recycle=25., Q_add=20., E_extract=65., R_aid=6., F_inert=25., W=220., M=7., H=240., T_prod=95.),
}
TOLERANCES = {"Grade A": {"W": 3., "M": 1., "H": 9.}, "Grade B": {"W": 6., "M": 1., "H": 15.}, "Grade C": {"W": 11., "M": 1., "H": 24.}}
PARAMS = dict(dt=1., tau_weight=1.5, delay_weight=1, gain_flow=.25, gain_concentration=50., gain_speed=-.03, gain_retention=1., gain_inert=.10, tau_moisture=4., delay_moisture=1, gain_flow_m=.01, gain_speed_m=.003, gain_add=.02, gain_heat=.12, gain_aux=.08, gain_extract=.025, tau_thickness=3., delay_thickness=1, gain_weight_h=.70, gain_moisture_h=2., gain_finish_h=.20, tau_temperature=2., delay_temperature=1, gain_heat_t=2., gain_aux_t=1., gain_speed_t=.01, warmup_steps=500, convergence_tolerance=.01)
PHASE_POINTS = {"steady_state": 0, "ramp": 8, "transient": 12, "stabilization": 6, "recovery": 15}
CONTROL_KEYS = ("Q_feed", "C_feed", "V_line", "P_heat", "P_aux", "Q_recycle", "Q_add", "E_extract", "R_aid", "F_inert")

