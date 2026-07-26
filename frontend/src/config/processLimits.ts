import type {ProcessInput} from '../types/api';

export const PROCESS_LIMITS: Partial<Record<keyof ProcessInput, readonly [number, number]>> = {
  Q_feed:[50,200], C_feed:[0.5,1.5], V_line:[100,2000], P_heat:[1,10], P_aux:[0,8],
  Q_recycle:[0,100], Q_add:[0,80], E_extract:[50,90], R_aid:[0,12], F_inert:[0,60],
  W:[30,300], M:[4,10], H:[70,300], T_prod:[20,140], D_supply:[0.8,1.2], D_act:[0.75,1], A_sensor:[0,1],
};

export function validateProcessInput(input: ProcessInput): string | undefined {
  for (const [key, limits] of Object.entries(PROCESS_LIMITS) as [keyof ProcessInput, readonly [number, number]][]) {
    const value=input[key];
    if (typeof value==='number' && (!Number.isFinite(value) || value<limits[0] || value>limits[1])) return `${key} must be between ${limits[0]} and ${limits[1]}.`;
  }
}
