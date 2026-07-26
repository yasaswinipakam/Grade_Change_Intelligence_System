from pydantic import BaseModel, Field, field_validator
from typing import Literal
from math import isfinite
class ProcessRequest(BaseModel):
    grade: Literal["Grade A","Grade B","Grade C"]; process_phase: Literal["steady_state","ramp","transient","stabilization","recovery"]="steady_state"
    Q_feed: float=Field(ge=50,le=200); C_feed: float=Field(ge=.5,le=1.5); V_line: float=Field(ge=100,le=2000); P_heat: float=Field(ge=1,le=10); P_aux: float=Field(ge=0,le=8); Q_recycle: float=Field(ge=0,le=100); Q_add: float=Field(ge=0,le=80); E_extract: float=Field(ge=50,le=90); R_aid: float=Field(ge=0,le=12); F_inert: float=Field(ge=0,le=60); W: float=Field(ge=30,le=300); M: float=Field(ge=4,le=10); H: float=Field(ge=70,le=300); T_prod: float=Field(ge=20,le=140); D_supply: float=Field(default=1,ge=.8,le=1.2); D_act: float=Field(default=1,ge=.75,le=1); A_sensor: float=Field(default=1,ge=0,le=1)
    @field_validator("*")
    @classmethod
    def finite(cls,v):
        if isinstance(v,float) and not isfinite(v): raise ValueError("must be finite")
        return v
