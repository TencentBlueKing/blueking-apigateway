import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

interface Iparams {
  id: number
  offset?: number
  limit?: number
}

// 获取环境列表
export const getStageList = ({ id, ...params }: Iparams) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${id}/stages/?${json2Query(params)}`);
