import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取告警策略列表
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const getStrategyList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/strategies/?${json2Query(data)}`);

/**
 *  创建告警策略
 * @param apigwId 网关id
 * @param data 创建参数
 */
export const createStrategy = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/strategies/`, data);

/**
 *  获取单个告警策略详情
 * @param apigwId 网关id
 * @param id 告警策略id
 */
export const getStrategyDetail = (apigwId: number, id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/strategies/${id}`);

/**
 *  更新告警策略
 * @param apigwId 网关id
 * @param id 告警策略id
 * @param data 更新参数
 */
export const updateStrategy = (apigwId: number, id: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/strategies/${id}`, data);

/**
 *  删除单个告警策略
 * @param apigwId 网关id
 * @param id 告警策略id
 */
export const deleteStrategy = (apigwId: number, id: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/strategies/${id}`);

/**
 *  更新告警策略状态
 * @param apigwId 网关id
 * @param id 告警策略id
 * @param data 更新状态参数
 */
export const updateStrategyStatus = (apigwId: number, id: number, data: any) => fetch.patch(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/strategies/${id}/status`, data);

/**
 *  获取告警记录统计
 * @param data 查询参数
 */
export const getRecordSummary = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/monitors/alarm/records/summary/?${json2Query(data)}`);

/**
 *  获取告警记录列表
 * @param apigwId 网关id
 * @param data 查询参数
 */
export const getRecordList = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/records/?${json2Query(data)}`);

/**
 *  获取某条告警记录详情
 * @param apigwId 网关id
 * @param id 告警记录id
 */
export const getRecordDetail = (apigwId: number, id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/monitors/alarm/records/${id}/`);
