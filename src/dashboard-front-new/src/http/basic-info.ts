import fetch from './fetch';
// import { json2Query } from '@/common/util';
import {  BasicInfoParams } from '@/views/basic-info/common/type';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取指定网关的信息
 * @param apigwId 网关id
 */
export const getGateWaysInfo = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/`);


/**
 *  更新网关状态，如启用、停用
 * @param apigwId 网关id
 * @param data 网关基本数据
 */
export const toggleGateWaysStatus = (apigwId: number, data: { status: number}) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/status`, data);

/**
 *  删除网关
 * @param apigwId 网关id
 * @param data 网关基本数据
 */
export const deleteGateWays = (apigwId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/`);

/**
 *  编辑网关基本信息
 * @param apigwId 网关id
 * @param data 网关基本数据
 */
export const editGateWays = (apigwId: number, data: BasicInfoParams) => fetch.patch(`${BK_DASHBOARD_URL}/gateways/${apigwId}/`, data);

/**
 *  更新网关基本信息
 * @param apigwId 网关id
 * @param data 网关基本数据
 */
export const getGatewaysLabels = (apigwId: number, data: BasicInfoParams) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/`, data);

