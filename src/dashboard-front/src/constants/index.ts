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
import { locale, t } from '@/locales';
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

// 插件图表列表
export const PLUGIN_ICONS = [
  'bk-cors', // 跨域资源共享插件
  'bk-header-rewrite', // 请求头重写插件
  'bk-ip-restriction', // IP限制插件
  'bk-rate-limit', // 限流插件
  'bk-mock', // Mock数据插件
  'api-breaker', // API断路器插件
  'request-validation', // 请求验证插件
  'fault-injection', // 故障注入插件
  'redirect', // 重定向插件
  'proxy-cache', // 代理缓存插件
  'proxy-mirror', // 代理镜像插件
  'csrf', // CSRF防护插件
  'uri-blocker', // URI阻断插件
  'response-rewrite', // 响应重写插件
  'serverless', // 无服务器插件
  'user-restriction', // 用户限制插件
];

// 插件图表列表 - 小号图表
export const PLUGIN_ICONS_MIN = [
  'bk-access-token-source',
  'bk-login-required',
  'bk-opentelemetry',
  'bk-query-string-rewrite',
  'proxy-cache',
  'traffic-label',
  'bk-request-body-limit',
  'bk-user-restriction',
  'bk-username-required',
];

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
        descriptionEn: None
      `,
};

// 自定义使用指引实例
export const CUSTOM_USAGE_GUIDE_EXAMPLE = {
  content: locale.value.indexOf('zh') > -1
    ? `# 代码自动检测

### 根据以下特征推断数据库类型（如 MySQL、PostgreSQL、Server）
连接字符串（JDBC URL、DSN 格式）
特殊语法（如 LIMIT vs TOP、字符串拼接符 || vs +）
特有函数（如 TO_CHAR() vs CONVERT()）
系统表/视图（如 information_schema vs pg_catalog）
给出多个可能的候选类型（按置信度排序）及判断依据。
版本范围推断`
    : `# Code automatic detection

### Infer database types based on the following characteristics (such as MySQL, PostgreSQL, Server)
Connection string (JDBC URL, DSN format)
Special syntax (such as Limit vs TOP, string concatenation | | vs+)
Unique functions (such as TO_CAR() vs CONVERT())
System tables/views (such as information_stemplate vs pg_catalog)
Provide multiple possible candidate types (ranked by confidence) and their criteria for judgment.
Version range inference`,
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
