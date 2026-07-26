import axios from 'axios'; import type {Decision,Health,ProcessInput} from '../types/api';
const client=axios.create({baseURL:import.meta.env.VITE_API_URL??'http://localhost:8000',timeout:12000});
export const decisionSupport=(input:ProcessInput)=>client.post<Decision>('/decision-support',input).then(r=>r.data);
export const health=()=>client.get<Health>('/health').then(r=>r.data);
