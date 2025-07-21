import http from '../http';

const path = '/gateways';

export interface IEventTemplate {
  description: string
  name: string
  step: number
}

export interface IEvent {
  id: number
  release_history_id: number
  name: string
  step: number
  status: 'doing' | 'success' | 'failure'
  created_time: string
  detail?: Record<string, any> | null
}

export interface ILogResponse {
  events: IEvent[]
  events_template: IEventTemplate[]
  status: string
}

export const createRelease = (apigwId: number, params: any) =>
  http.post(`${path}/${apigwId}/releases/`, params);

export const getReleaseEvents = (apigwId: number, historyId: number) =>
  http.get<ILogResponse>(`${path}/${apigwId}/releases/histories/${historyId}/events/`);

export const getReleaseHistories = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/releases/histories/`, params);
