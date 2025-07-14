import http from '../http';
/**
 * 获取环境列表
 * @param apigwId 网关id
 */
export function getStageList(apigwId: number) {
  return http.get<{ apigwId: number }>(`/gateways/${apigwId}/stages/`);
}
