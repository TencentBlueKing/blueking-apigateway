import http from '../http';

const path = '';

/**
 * 当前用户信息
 */
export function getUserInfo() {
  return http.get<{
    avatar_url: string
    chinese_name: string
    display_name: string
    tenant_id: string | null
    username: string
  }>(`${path}/accounts/userinfo/`);
}

/**
 * 当前环境相关配置
 */
export function getFeatureFlags(params: {
  limit?: number
  offset?: number
}) {
  return http.get<{
    ALLOW_CREATE_APPCHAT: boolean
    ALLOW_UPLOAD_SDK_TO_REPOSITORY: boolean
    ENABLE_AI_COMPLETION: boolean
    ENABLE_BK_NOTICE: boolean
    ENABLE_MONITOR: boolean
    ENABLE_MULTI_TENANT_MODE: boolean
    ENABLE_RUN_DATA: boolean
    ENABLE_RUN_DATA_METRICS: boolean
    ENABLE_SDK: boolean
    GATEWAY_APP_BINDING_ENABLED: boolean
    MENU_ITEM_ESB_API: boolean
    MENU_ITEM_ESB_API_DOC: boolean
    SYNC_ESB_TO_APIGW_ENABLED: boolean
  }>(`${path}/settings/feature_flags/`, params);
}

/**
 * 当前环境相关配置
 */
export function getEnv() {
  return http.get<{
    BK_API_RESOURCE_URL_TMPL: string
    BK_APP_CODE: string
    BK_COMPONENT_API_URL: string
    BK_DASHBOARD_CSRF_COOKIE_NAME: string
    BK_DASHBOARD_FE_URL: string
    BK_DASHBOARD_URL: string
    BK_DEFAULT_TEST_APP_CODE: string
    BK_PAAS_APP_REPO_URL_TMPL: string
    EDITION: string
  }>(`${path}/settings/env-vars/`);
}
