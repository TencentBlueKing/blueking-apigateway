/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
import { t } from '@/locales';
// 方法名称
export const HTTP_METHODS = [
  {
    id: 'GET',
    name: 'GET',
  },
  {
    id: 'POST',
    name: 'POST',
  },
  {
    id: 'PUT',
    name: 'PUT',
  },
  {
    id: 'PATCH',
    name: 'PATCH',
  },
  {
    id: 'DELETE',
    name: 'DELETE',
  },
  {
    id: 'HEAD',
    name: 'HEAD',
  },
  {
    id: 'OPTIONS',
    name: 'OPTIONS',
  },
  {
    id: 'ANY',
    name: 'ANY',
  },
];

// 授权维度
export const AUTHORIZATION_DIMENSION = [
  {
    id: 'api',
    name: t('按网关'),
  },
  {
    id: 'resource',
    name: t('按资源'),
  },
];

// 时间维度
export const EXPIRE_DAYS_CONSTANTS = [
  {
    label: t('永久'),
    value: 0,
  },
  {
    label: t('6个月'),
    value: 180,
  },
  {
    label: t('12个月'),
    value: 360,
  },
];

// 插件 code 对应的 AgIcon 名称
export const PLUGIN_ICONS = new Map([
  ['api-breaker', 'plugin-api-breaker'],
  ['bk-access-token-source', 'plugin-bk-access-token-source'],
  ['bk-cors', 'plugin-bk-cors'],
  ['bk-header-rewrite', 'plugin-bk-header-rewrite'],
  ['bk-ip-restriction', 'plugin-bk-ip-restriction'],
  ['bk-login-required', 'plugin-bk-login-required'],
  ['bk-mock', 'plugin-bk-mock'],
  ['bk-opentelemetry', 'plugin-bk-opentelemetry'],
  ['bk-query-string-rewrite', 'plugin-bk-query-string-rewrite'],
  ['bk-rate-limit', 'plugin-bk-rate-limit'],
  ['bk-request-body-limit', 'plugin-bk-request-body-limit'],
  ['bk-resource-user-rate-limit', 'plugin-bk-resource-user-rate-limit'],
  ['bk-traffic-label', 'plugin-bk-traffic-label'],
  ['bk-user-restriction', 'plugin-user-restriction'],
  ['bk-username-required', 'bk-username-required'],
  ['fault-injection', 'plugin-fault-injection'],
  ['proxy-cache', 'plugin-proxy-cache'],
  ['proxy-mirror', 'plugin-proxy-mirror'],
  ['redirect', 'plugin-redirect'],
  ['request-validation', 'plugin-request-validation'],
  ['response-rewrite', 'plugin-response-rewrite'],
  ['serverless', 'plugin-serverless'],
  ['uri-blocker', 'plugin-uri-blocker'],
  ['user-restriction', 'plugin-user-restriction'],
]);

// 资源导入示例
export const RESOURCE_IMPORT_EXAMPLE = {
  content: `\
# Swagger yaml format template example
openapi: 3.0.1
servers:
- url: /
info:
  version: '2.0'
  title: API Gateway Resources
  description: ''
paths:
  /users/:
    get:
      operationId: get_users
      description: get users
      tags: []
      x-bk-apigateway-resource:
        isPublic: true
        allowApplyPermission: true
        matchSubpath: false
        enableWebsocket: false
        backend:
          method: get
          path: /users/
          matchSubpath: false
          timeout: 30
        pluginConfigs: []
        authConfig:
          userVerifiedRequired: false
          appVerifiedRequired: true
          resourcePermissionRequired: true
          oauth2PersonalClientEnabled: false
          oauth2PublicClientEnabled: false
        descriptionEn: None
      `,
};

// 使用指引
export const USAGE_GUIDE_LIST = [
  {
    label: t('默认使用指引'),
    value: 'default',
  },
  {
    label: t('自定义使用指引'),
    value: 'custom',
  },
];

// MCPSever连接方式
export const MCP_PROTOCOL_TYPE = [
  {
    label: 'Streamable HTTP',
    value: 'streamable_http',
  },
  {
    label: 'SSE',
    value: 'sse',
  },
];

//  MCP详情选项卡
export const MCP_TAB_LIST = [
  {
    name: 'tools',
    label: t('工具'),
  },
  {
    name: 'prompts',
    label: 'Prompts',
  },
  {
    name: 'auth',
    label: t('已授权应用'),
  },
  {
    name: 'guide',
    label: t('使用指引'),
  },
].map((item) => {
  return {
    ...item,
    count: 0,
    show: true,
  };
});

// 状态列表
export const STATUS_LIST = [
  {
    name: t('全部'),
    id: 'all',
  },
  {
    name: t('成功'),
    id: 'success',
  },
  {
    name: t('失败'),
    id: 'failed',
  },
];

// 定时刷新时间列表
export const INTERVAL_TIME_LIST = [
  {
    label: 'Off',
    value: 'off',
  },
  {
    label: '5s',
    value: '5s',
  },
  {
    label: '10s',
    value: '10s',
  },
  {
    label: '15s',
    value: '15s',
  },
  {
    label: '30s',
    value: '30s',
  },
  {
    label: '1m',
    value: '1m',
  },
  {
    label: '5m',
    value: '5m',
  },
  {
    label: '15m',
    value: '15m',
  },
  {
    label: '30m',
    value: '30m',
  },
  {
    label: '1h',
    value: '1h',
  },
  {
    label: '2h',
    value: '2h',
  },
  {
    label: '1d',
    value: '1d',
  },
];

// 精度刷新时间列表
export const PRECISION_STEPS_LIST = [
  {
    label: 'Auto',
    value: 'auto',
  },
  {
    label: '1m',
    value: '1m',
  },
  {
    label: '5m',
    value: '5m',
  },
  {
    label: '10m',
    value: '10m',
  },
  {
    label: '30m',
    value: '30m',
  },
  {
    label: '1h',
    value: '1h',
  },
  {
    label: '3h',
    value: '3h',
  },
  {
    label: '12h',
    value: '12h',
  },
];

// 已授权应用操作类型列表
export const AUTHORIZATION_APPLICATION_OPERATE_TYPE = [
  {
    name: t('主动授权'),
    id: 'grant',
  },
  {
    name: t('申请审批'),
    id: 'apply',
  },
];

// 授权维度列表
export const GRANT_DIMENSION_TYPE_LIST = [
  {
    label: t('按网关'),
    value: 'api',
  },
  {
    label: t('按资源'),
    value: 'resource',
  },
];

// 资源类型列表
export const RESOURCE_TYPE_LIST = [
  {
    label: t('普通 API'),
    value: 'standard',
    theme: 'default',
    description: t('将后端服务暴露为 API 资源，可配置 MCP Tool'),
  },
  {
    label: t('模型代理 API'),
    value: 'ai',
    theme: 'info',
    description: t('固定 POST，引用一个模型服务，暴露 OpenAI 兼容的 chat/completions'),
  },
];
