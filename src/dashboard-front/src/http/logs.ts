import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;

export interface IEventTemplate {
  description: string
  name: string
  step: number
}

export interface IEvent {
  id: number;
  release_history_id: number;
  name: string;
  step: number;
  status: 'doing' | 'success' | 'failure';
  created_time: string;
  detail?: Record<string, any> | null;
}

export interface ILogResponse {
  events: IEvent[]
  events_template: IEventTemplate[]
  status: string
}

/**
 *  查询发布事件(日志)
 * @param apigwId 网关id
 * @param historyId 历史id
 * @returns ILogResponse
 */
export const getLogs = (apigwId: number, historyId: number): Promise<ILogResponse> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/histories/${historyId}/events/`);

/**
 *  版本发布接口
 * @param apigwId 网关id
 * @param data 数据
 * @returns
 */
export const createReleases = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/`, data, { globalError: false });
