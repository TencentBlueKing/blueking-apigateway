import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

export const getUser = () => fetch.get(`${BK_DASHBOARD_URL}/accounts/userinfo/`);

export const getFeatureFlags = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/settings/feature_flags/?${json2Query(data)}`);
