import {useState} from 'react';
import {PROCESS_LIMITS,validateProcessInput} from '../config/processLimits';
import type {ProcessInput} from '../types/api';

export const SCENARIOS: Record<'A'|'B'|'C', ProcessInput> = {
 A:{grade:'Grade B',process_phase:'steady_state',Q_feed:140,C_feed:1,V_line:900,P_heat:7,P_aux:4,Q_recycle:35,Q_add:15,E_extract:70,R_aid:4,F_inert:20,W:120,M:6,H:150,T_prod:85,D_supply:1,D_act:1,A_sensor:1},
 B:{grade:'Grade C',process_phase:'ramp',Q_feed:190,C_feed:1.1,V_line:720,P_heat:7.1,P_aux:4,Q_recycle:35,Q_add:25,E_extract:70,R_aid:4,F_inert:20,W:220,M:7,H:240,T_prod:85,D_supply:1,D_act:1,A_sensor:1},
 C:{grade:'Grade A',process_phase:'transient',Q_feed:165,C_feed:1.05,V_line:840,P_heat:7.2,P_aux:4,Q_recycle:35,Q_add:18,E_extract:70,R_aid:4,F_inert:20,W:155,M:6.4,H:175,T_prod:85,D_supply:1,D_act:1,A_sensor:1},
};

export function ProcessInputForm({value,onChange,onSubmit,loading}:{value:ProcessInput;onChange:(value:ProcessInput)=>void;onSubmit:()=>void;loading:boolean}){
 const [validationError,setValidationError]=useState(''); const keys=(Object.keys(value).filter(k=>!['grade','process_phase'].includes(k)) as (keyof ProcessInput)[]); const update=(next:ProcessInput)=>{setValidationError('');onChange(next)}; const submit=()=>{const error=validateProcessInput(value);if(error){setValidationError(error);return}onSubmit()};
 return <section className="manual-controls">
  <div className="control-pair"><label>Grade<select value={value.grade} onChange={e=>update({...value,grade:e.target.value as ProcessInput['grade']})}><option>Grade A</option><option>Grade B</option><option>Grade C</option></select></label><label>Phase<select value={value.process_phase} onChange={e=>update({...value,process_phase:e.target.value as ProcessInput['process_phase']})}>{['steady_state','ramp','transient','stabilization','recovery'].map(x=><option key={x}>{x}</option>)}</select></label></div>
  <div className="fields">{keys.map(key=>{const limits=PROCESS_LIMITS[key];return <label key={key}>{key}<input type="number" step="any" min={limits?.[0]} max={limits?.[1]} value={value[key] as number} onChange={e=>update({...value,[key]:Number(e.target.value)})}/>{limits&&<small>{limits[0]}–{limits[1]}</small>}</label>})}</div>
  {validationError&&<p className="input-error">{validationError}</p>}<button className="run-button" disabled={loading} onClick={submit}>{loading?'Analyzing process…':'Run decision support'}</button>
 </section>
}
