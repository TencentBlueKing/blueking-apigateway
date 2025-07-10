import type { IApiGateway, IApiGatewayDetail } from '@/types/gateway';
import http from '../http';

const path = '/gateways';

export function getGatewayList(params: {
  limit?: number
  offset?: number
} = {}) {
  return http.get<{
    count: number
    results: IApiGateway[]
  }>(`${path}/`, params);
}

export function getGatewayDetail(id: number) {
  return http.get<IApiGatewayDetail>(`${path}/${id}/`);
}
