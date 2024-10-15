import fetch from './fetch';
import { json2Query, blobDownLoad  } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

export interface IBatchUpdateParams {
  resource_dimension_ids: number[]
  gateway_dimension_ids: number[]
  expire_days: 0 | 180 | 360
}

// 导出参数interface
export interface IExportParams {
  [key: string | number]: unknown
  export_type: string
  bk_app_code?: string
  keyword?: string
  resource_ids?: number
  resource_name?: string
  resource_permission_ids?: Array<number>
  gateway_permission_ids?: Array<number>
  grant_type?: string
  dimension?: string
}

// 搜索参数
export interface IFilterParams {
  [key: string | number]: unknown
  bk_app_code?: string
  keyword?: string
  resource_id?: number
  grant_dimension?: string
}

export interface IAuthData {
  bk_app_code: string;
  expire_type: string;
  expire_days: number | null;
  resource_ids: number[];
  dimension: string;
}

/**
 *  获取权限申请单列表--apply
 * @param apigwId 网关id
 * @param data
 */
export const getPermissionApplyList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-apply/?${json2Query(data)}`);

/**
 *  审批操作
 * @param apigwId 网关id
 * @param data 审批参数
 */
export const updatePermissionStatus = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-apply/approval/`, data);

/**
 *  获取权限申请单详情
 * @param apigwId 网关id
 * @param id
 */
export const getPermissionApplyDetail = (apigwId: number, id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-apply/${id}/`);


/**
 *  获取权限申请记录列表--records
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const getPermissionRecordList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-records/?${json2Query(data)}`);

/**
 *  获取权限申请记录列表获取权限申请记录详情
 * @param apigwId 网关id
 * @param id
 */
export const getPermissionRecordDetail = (apigwId: number, id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-records/?${id}`);


/**
 *  获取网关权限列表--api
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const getApiPermissionList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/?${json2Query(data)}`);

/**
 *  网关权限主动授权
 * @param apigwId 网关id
 * @param data 授权参数
 */
export const authApiPermission = (apigwId: number, data: IAuthData) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/`, data);

/**
 *  获取有网关权限的应用列表
 * @param apigwId 网关id
 */
export const getApiPermissionAppList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/bk-app-codes/`);

/**
 *  网关权限删除
 * @param apigwId 网关id
 * @param data 删除参数
 */
export const deleteApiPermission = (apigwId: number, data: { ids: number[] }) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/delete/?${json2Query(data)}`);

/**
 *  网关权限导出
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportApiPermission = async (apigwId: number, data: any) => {
  const res = await fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  网关权限续期
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const batchUpdateApiPermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/renew/`, data);

/**
 *  获取权限列表
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const fetchPermissionList = (apigwId: number, data: IFilterParams) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permissions/?${json2Query(data)}`);

/**
 *  获取资源权限列表--resource
 *  弃用
 * @param apigwId 网关id
 * @param data 查询参数
 */
// export const getResourcePermissionList = (apigwId: number, data: any) => fetch.get(
//   `${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-resource-permissions/?${json2Query(data)}`
// );

/**
 *  资源权限主动授权
 * @param apigwId 网关id
 * @param data 授权参数
 */
export const authResourcePermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-resource-permissions/`, data);

/**
 *  获取有资源权限的应用列表
 * @param apigwId 网关id
 */
export const getResourcePermissionAppList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permissions/bk-app-codes/`);

/**
 *  获取有资源权限的应用列表
 *  弃用
 * @param apigwId 网关id
 */
// export const getResourcePermissionAppList = (apigwId: number) => fetch.get(
//   `${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-resource-permissions/bk-app-codes/`
// );

/**
 *  删除资源权限
 * @param apigwId 网关id
 * @param data 删除参数
 */
export const deleteResourcePermission = (apigwId: number, data: { ids: number[] }) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-resource-permissions/delete/?${json2Query(data)}`);

/**
 *  资源权限导出
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportPermissionList = async (apigwId: number, data: IExportParams) => {
  const res = await fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permissions/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  资源权限导出
 *  弃用
 * @param apigwId 网关id
 * @param data 导出参数
 */
// export const exportPermissionList = async (apigwId: number, data: any) => {
//   const res = await fetch.post(
//     `${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-resource-permissions/export/`,
//     data,
//     { responseType: 'blob' }
//   );
//   return blobDownLoad(res);
// };

/**
 *  批量权限续期
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const batchUpdatePermission = (apigwId: number, data: IBatchUpdateParams) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permissions/renew/`, data);

/**
 *  单个资源权限续期
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const updateResourcePermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-resource-permissions/renew/`, data);
