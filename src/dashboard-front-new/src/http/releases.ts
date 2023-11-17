import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;


/**
 * 生成资源版本
 * @param apigwId 网关id
 * @param data 资源版本信息
 */
export const getReleaseHistories = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/histories?${json2Query(data)}`);
