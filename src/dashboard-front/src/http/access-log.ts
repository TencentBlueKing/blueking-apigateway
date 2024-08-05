import fetch from './fetch';
import { json2Query } from '@/common/util';
import {  ChartInterface, LogDetailInterface } from '@/views/operate-data/access-log/common/type';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取流程日志列表
 * @param apigwId 网关id
 */
export const fetchApigwAccessLogList = (apigwId: number, params: ChartInterface, extraStr?: string) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/logs/?${json2Query(params)}${extraStr}`);

/**
 *  获取流程日志chart
 * @param apigwId 网关id
 */
export const fetchApigwAccessLogChart = (apigwId: number, params: ChartInterface, extraStr?: string)  => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/logs/timechart/?${json2Query(params)}${extraStr}`);

/**
 *  获取流程日志link
 * @param apigwId 网关id
 */
export const fetchApigwAccessLogShareLink = (apigwId: number, params: { request_id: string }) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/logs/${params.request_id}/link/`);

/**
 *  获取流程日志详情
 * @param apigwId 网关id
 */
export const fetchApigwAccessLogDetail = (apigwId: number, requestId: string, params: LogDetailInterface) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/logs/${requestId}/?${json2Query(params)}`);


/**
 *  获取stage数据
 * @param apigwId 网关id
 */
export const fetchApigwStages = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/?${json2Query(params)}`);
