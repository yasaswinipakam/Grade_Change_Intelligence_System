export type Grade='Grade A'|'Grade B'|'Grade C'; export type Phase='steady_state'|'ramp'|'transient'|'stabilization'|'recovery';
export interface ProcessInput {grade:Grade;process_phase:Phase;Q_feed:number;C_feed:number;V_line:number;P_heat:number;P_aux:number;Q_recycle:number;Q_add:number;E_extract:number;R_aid:number;F_inert:number;W:number;M:number;H:number;T_prod:number;D_supply:number;D_act:number;A_sensor:number}
export interface Contributor {feature:string;value:number;shap_value:number;direction:string;operator_message:string}
export interface Action {control:string;priority:string;recommendation:string;recommended_direction:string;expected_effect:{basis_weight_deviation:string;off_spec_probability:string};confidence:string;operator_message:string}
export interface Validated {validation_state:string;validation_reason:string;validated_recommendation:string|null;approved_step_size:string;ready_for_execution:boolean;operator_message:string}
export interface Decision {request_id:string;prediction:{basis_weight_deviation:number;off_spec_probability:number};explanation:{top_contributors:Contributor[]};recommendations:Action[];validated_recommendations:Validated[]}
export interface Health {status:string;model_loaded:boolean;shap_loaded:boolean;constraints_loaded:boolean}
