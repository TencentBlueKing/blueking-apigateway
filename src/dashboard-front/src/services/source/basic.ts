/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
import http from '../http';
import { useEnv } from '@/stores';

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
    ENABLE_DISPLAY_NAME_RENDER: boolean
    ENABLE_GATEWAY_OPERATION_STATUS: boolean
    ENABLE_HEALTH_CHECK: boolean
    ENABLE_MCP_SERVER_PROMPT: boolean
    ENABLE_MONITOR: boolean
    ENABLE_MULTI_TENANT_MODE: boolean
    ENABLE_RUN_DATA: boolean
    ENABLE_RUN_DATA_METRICS: boolean
    ENABLE_SDK: boolean
    GATEWAY_APP_BINDING_ENABLED: boolean
    MENU_ITEM_ESB_API: boolean
    MENU_ITEM_ESB_API_DOC: boolean
    SYNC_ESB_TO_APIGW_ENABLED: boolean
  }>(`${path}/settings/feature-flags/`, params);
}

/**
 * 当前环境相关配置
 */
export function getEnv() {
  return http.get<{
    BK_ANALYSIS_SCRIPT_SRC: string
    BK_APIGATEWAY_VERSION: string
    BK_APISIX_DOC_URL: string
    BK_APISIX_URL: string
    BK_API_RESOURCE_URL_TMPL: string
    BK_APP_CODE: string
    BK_COMPONENT_API_URL: string
    BK_DASHBOARD_COOKIE_DOMAIN: string
    BK_DASHBOARD_CSRF_COOKIE_DOMAIN: string
    BK_DASHBOARD_CSRF_COOKIE_NAME: string
    BK_DASHBOARD_FE_URL: string
    BK_DASHBOARD_URL: string
    BK_DEFAULT_TEST_APP_CODE: string
    BK_DOCS_URL_PREFIX: string
    BK_LOGIN_URL: string
    BK_PAAS_APP_REPO_URL_TMPL: string
    BK_SHARED_RES_URL: string
    BK_USER_WEB_API_URL: string
    CREATE_CHAT_API: string
    EDITION: string
    SEND_CHAT_API: string
    HELPER: {
      name: string
      href: string
    }
    DOC_LINKS: {
      GUIDE: string
      QUERY_USE: string
      USER_VERIFY: string
      TEMPLATE_VARS: string
      AUTH: string
      SWAGGER: string
      CORS: string
      BREAKER: string
      RATELIMIT: string
      JWT: string
      USER_TYPE: string
      ERROR_CODE: string
      COMPONENT_RATE_LIMIT: string
      COMPONENT_CREATE_API: string
      IMPORT_RESOURCE_DOCS: string
      INSTANCE_TYPE: string
      USER_API: string
      UPGRADE_TO_113_TIP: string
      MCP_SERVER_PERMISSION_APPLY: string
      PLUGIN_AI_PROXY: string
      PLUGIN_AI_RATE_LIMITING: string
      PLUGIN_API_BREAKER: string
      PLUGIN_BK_ACCESS_TOKEN_SOURCE: string
      PLUGIN_BK_CORS: string
      PLUGIN_BK_HEADER_REWRITE: string
      PLUGIN_BK_IP_RESTRICTION: string
      PLUGIN_BK_MOCK: string
      PLUGIN_BK_RATE_LIMIT: string
      PLUGIN_BK_REQUEST_BODY_LIMIT: string
      PLUGIN_BK_USERNAME_REQUIRED: string
      PLUGIN_BK_USER_RESTRICTION: string
      PLUGIN_FAULT_INJECTION: string
      PLUGIN_PROXY_CACHE: string
      PLUGIN_REDIRECT: string
      PLUGIN_REQUEST_VALIDATION: string
      PLUGIN_RESPONSE_REWRITE: string
      PLUGIN_URI_BLOCKER: string
    }
  }>(`${path}/settings/env-vars/`);
}

/**
 * 获取多租户人员
 */
export function getTenantUsers(
  params: { keyword: string },
  tenant_id: string,
) {
  const envStore = useEnv();
  return http.get(
    `${envStore.env.BK_USER_WEB_API_URL}/api/v3/open-web/tenant/users/-/search/`,
    params,
    { headers: { 'X-Bk-Tenant-Id': tenant_id || '' } },
  );
}

/**
 * 获取版本日志
 */
export const getVersionLog = () => http.get('/version-log/');

/**
 * 将国际化语言设置保存到用户管理中
 */
export const saveUserLanguage = (
  url: string,
  params: { language: string },
  tenant_id: string | null,
) =>
  http.put(url, params, tenant_id ? { headers: { 'X-Bk-Tenant-Id': tenant_id || '' } } : {});
