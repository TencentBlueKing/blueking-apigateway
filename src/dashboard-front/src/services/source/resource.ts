import http from '../http';

const path = '/gateways';

export interface IVersionItem {
  id: number | string
  released_stages: {
    id: number
    name: string
  }[]
  sdk_count: number
  version: string
  schema_version: string
  comment: string
  created_time: string
  created_by: string
}

export interface IDiffData {
  add: Record<string, any>[]
  delete: Record<string, any>[]
  update: {
    source: Record<string, any>
    target: Record<string, any>
  }[]
}

export const getVersionList = (apigwId: number, params: {
  limit?: number
  offset?: number
}) =>
  http.get<{
    count: number
    results: IVersionItem[]
  }>(`${path}/${apigwId}/resource-versions/`, params);

// 资源版本详情
export const getVersionDetail = (apigwId: number, id: number, params?: any) =>
  http.get(`${path}/${apigwId}/resource-versions/${id}/`, params);

export const getVersionDiff = (apigwId: number, data: {
  source_resource_version_id: number
  target_resource_version_id: number
}) =>
  http.get<IDiffData>(`${path}/${apigwId}/resource-versions/diff/`, data);

/**
 *  过滤出需要认证用户的资源列表，免用户认证应用白名单插件，需要使用此数据过滤资源
 * @param apigwId 网关id
 * @param params 参数
 */
export const getVerifiedUserRequiredResources = (apigwId: number, params?: {
  limit?: number
  offset?: number
}) =>
  http.get(`${path}/${apigwId}/resources/with/verified-user-required/`, params);
