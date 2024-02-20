import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  批量审批
 * @param data 数据
 */
export const applyRecordsHandle = (data: any) => fetch.post(`${BK_DASHBOARD_URL}/esb/permissions/apply-records/handle/`, data);

/**
 *  获取待审批的申请单列表
 * @param data 数据
 */
export const applyRecordsPending = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/permissions/apply-records/pending/?${json2Query(data)}`);
