import fetch from './fetch';
import { json2Query } from '@/common/util';
import { DefaultSearchParamsInterface } from '@/views/operate-records/common/type';

const { BK_DASHBOARD_URL } = window;

/**
 *  查询操作记录
 * @param apigwId 网关id
 * @returns
 */
export const fetchApigwAuditLogs = (apigwId: number, params: DefaultSearchParamsInterface) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/audits/logs/?${json2Query(params)}`);
