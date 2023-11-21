import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;


/**
 * 发布历史列表获取接口
 * @param apigwId 网关id
 * @param data 资源版本信息
 */
export const getReleaseHistories = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/histories?${json2Query(data)}`);

/**
 * 发布详情接口
 * @param apigwId 网关id
 * @param data 资源版本信息
 */
export const getReleaseLatest = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/histories/latest/`);
