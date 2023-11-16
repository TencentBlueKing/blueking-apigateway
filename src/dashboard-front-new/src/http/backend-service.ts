import fetch from './fetch';
import { json2Query } from '@/common/util';
const { BK_DASHBOARD_URL } = window;


/**
 *  获取后端服务列表
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const getBackendServiceList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/?${json2Query(data)}`);

/**
 *  创建后端服务
 * @param apigwId 网关id
 * @param data 新建参数
 */
export const createBackendService = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/`, data);

/**
 *  获取后端服务详情
 * @param apigwId 网关id
 * @param id 后端服务id
 */
export const getBackendServiceDetail = (apigwId: number, id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/${id}/`);

/**
 *  更新后端服务
 * @param apigwId 网关id
 * @param data 更新参数
 * @param id 后端服务id
 */
export const updateBackendService = (apigwId: number, id: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/${id}/`, data);

/**
 *  删除后端服务
 * @param apigwId 网关id
 * @param id 后端服务id
 */
export const deleteBackendService = (apigwId: number, id: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/${id}/`);
