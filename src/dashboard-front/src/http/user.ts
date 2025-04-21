import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL, BK_USER_WEB_API_URL } = window;

export const getUser = () => fetch.get(`${BK_DASHBOARD_URL}/accounts/userinfo/`);

export const getFeatureFlags = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/settings/feature_flags/?${json2Query(data)}`);

export const getVersionLog = () => fetch.get(`${BK_DASHBOARD_URL}/version-log`);

export const searchTenantUsers = (
  data: {
    keyword: string
  },
  tenant_id: string,
) => fetch.get(
  `${BK_USER_WEB_API_URL}/api/v3/open-web/tenant/users/-/search/?${json2Query(data)}`,
  undefined,
  {
    headers: {
      'X-Bk-Tenant-Id': tenant_id || '',
    },
  },
);

export const changeTenantLocales = (
  tenant_id: string,
  data: {
    language: string
  },
) => fetch.put(
  `${BK_USER_WEB_API_URL}/api/v3/open-web/tenant/current-user/language/`,
  data,
  {
    headers: {
      'X-Bk-Tenant-Id': tenant_id || '',
    },
  },
);
