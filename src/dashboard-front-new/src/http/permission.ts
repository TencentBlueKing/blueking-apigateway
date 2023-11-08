import fetch from './fetch';
import { json2Query  } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取权限申请单列表--apply
 * @param apigwId 网关id
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
export const authApiPermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/?${json2Query(data)}`);

/**
 *  获取有网关权限有权限的应用列表
 * @param apigwId 网关id
 */
export const getApiPermissionAppList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/bk-app-codes/`);

/**
 *  网关权限删除
 * @param apigwId 网关id
 * @param data 删除参数
 */
export const deleteApiPermission = (apigwId: number, data: any) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/delete/`, data);

/**
 *  网关权限导出
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportApiPermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/export/`, data);

/**
 *  网关权限续期
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const batchUpdateApiPermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-gateway-permissions/renew/`, data);


/**
 *  获取资源权限列表--resource
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const getResourcePermissionList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-Resource-permissions/?${json2Query(data)}`);

/**
 *  资源权限主动授权
 * @param apigwId 网关id
 * @param data 授权参数
 */
export const authResourcePermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-Resource-permissions/?${json2Query(data)}`);

/**
 *  获取有资源权限的应用列表
 * @param apigwId 网关id
 */
export const getResourcePermissionAppList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-Resource-permissions/bk-app-codes/`);

/**
 *  删除资源权限
 * @param apigwId 网关id
 * @param data 删除参数
 */
export const deleteResourcePermission = (apigwId: number, data: any) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-Resource-permissions/delete/`, data);

/**
 *  资源权限导出
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportResourcePermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-Resource-permissions/export/`, data);

/**
 *  资源权限续期
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const batchUpdateResourcePermission = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/permissions/app-Resource-permissions/renew/`, data);
