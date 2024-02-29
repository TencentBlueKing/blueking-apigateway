import fetch from './fetch';
// import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  查询 runner
 * @param timeRange 查询运行时间
 */
export const getApigwRuntime = ({ timeRange }: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/status/systems/summary/?time_since=${timeRange}`);

/**
 *  查询 time-line
 * @param
 */
export const getApigwTimeline = () => fetch.get(`${BK_DASHBOARD_URL}/esb/status/systems/events/timeline/`);

export const getApigwSystemSummary = ({  system, start, end }: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/status/systems/${system}/summary/?time_since=custom&mts_start=${start}&mts_end=${end}`);

export const getApigwChartDetail = ({  system, start, end }: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/status/systems/${system}/date-histogram/?time_interval=1m&mts_start=${start}&mts_end=${end}`);

export const getApigwRuntimeRequest = ({ type, system, start, end }: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/status/systems/${system}/details/group-by/?time_since=custom&mts_start=${start}&mts_end=${end}&group_by=${type}&order=availability_asc`);

export const getApigwErrorRequest = ({   system, appCode, requestUrl, componentName, start, end }: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/status/systems/${system}/errors/?url=${requestUrl}&app_code=${appCode}&component_name=${componentName}&mts_start=${start}&mts_end=${end}&size=200`);
