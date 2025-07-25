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
import { defineStore } from 'pinia';
import { getEnv } from '@/services/source/basic';
import { locale } from '@/locales';

export const useEnv = defineStore('useEnv', {
  state: () => ({
    env: {
      BK_API_RESOURCE_URL_TMPL: '',
      BK_APP_CODE: '',
      BK_COMPONENT_API_URL: '',
      BK_DASHBOARD_CSRF_COOKIE_NAME: '',
      BK_DASHBOARD_FE_URL: '',
      BK_DASHBOARD_URL: '',
      BK_DEFAULT_TEST_APP_CODE: '',
      BK_PAAS_APP_REPO_URL_TMPL: '',
      EDITION: '',
      BK_APIGATEWAY_VERSION: '',
      BK_DOCS_URL_PREFIX: '',
      BK_USER_WEB_API_URL: '',
      BK_LOGIN_URL: '',
      BK_ANALYSIS_SCRIPT_SRC: '',
      CREATE_CHAT_API: '',
      SEND_CHAT_API: '',
      HELPER: {
        name: '',
        href: '',
      },
    },
  }),
  getters: {
    docsURLPrefix: (state) => {
      const lang = locale.value === 'zh-cn' ? 'ZH' : 'EN';
      const docVersion = (state.env.BK_APIGATEWAY_VERSION || '1.17.0').split('.').slice(0, 2).join('.');
      return `${state.env.BK_DOCS_URL_PREFIX}/markdown/${lang}/APIGateway/${docVersion}`;
    },
    doc() {
      return {
        // 使用指南
        GUIDE: `${this.docsURLPrefix}/UserGuide/README.md`,
        // “请求流水查询规则”
        QUERY_USE: `${this.docsURLPrefix}/UserGuide/Explanation/access-log.md`,
        // 蓝鲸用户认证
        USER_VERIFY: `${this.docsURLPrefix}/UserGuide/Explanation/authorization.md`,
        // API资源模板变量
        TEMPLATE_VARS: `${this.docsURLPrefix}/UserGuide/Explanation/template-var.md`,
        // 网关认证
        AUTH: `${this.docsURLPrefix}/UserGuide/Explanation/authorization.md`,
        // Swagger说明文档
        SWAGGER: `${this.docsURLPrefix}/UserGuide/HowTo/Connect/swagger-explain.md`,
        // 跨域资源共享(CORS)
        CORS: `${this.docsURLPrefix}/UserGuide/HowTo/Plugins/cors.md`,
        // 断路器
        BREAKER: `${this.docsURLPrefix}/UserGuide/HowTo/Plugins/circuit-breaker.md`,
        // 频率控制
        RATELIMIT: `${this.docsURLPrefix}/UserGuide/HowTo/Plugins/rate-limit.md`,
        // JWT
        JWT: `${this.docsURLPrefix}/UserGuide/Explanation/jwt.md`,
        // 用户类型
        USER_TYPE: `${this.docsURLPrefix}/UserGuide/README.md`,
        // API网关错误码
        ERROR_CODE: `${this.docsURLPrefix}/UserGuide/FAQ/error-response.md`,
        // 组件频率控制
        COMPONENT_RATE_LIMIT: `${this.docsURLPrefix}/component/reference/rate-limit.md`,
        // 如何开发和发布组件
        COMPONENT_CREATE_API: `${this.docsURLPrefix}/component/quickstart/create-api.md`,
        // 文档导入详情
        IMPORT_RESOURCE_DOCS: `${this.docsURLPrefix}/UserGuide/HowTo/Connect/manage-document.md`,
        // 实例类型
        INSTANCE_TYPE: `${this.docsURLPrefix}/`,
        // 调用API
        USER_API: `${this.docsURLPrefix}/UserGuide/HowTo/call-gateway-api.md`,
        // 升级到 1.13 的指引说明
        UPGRADE_TO_113_TIP: '',
        // mcp 权限申请指引
        MCP_SERVER_PERMISSION_APPLY: `${this.docsURLPrefix}/UserGuide/HowTo/apply-mcp-server-permission.md`,
      };
    },
    userSelectorAPI: state => `${state.env.BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fs_list_users/`,
  },
  actions: {
    /**
     * 查询环境变量信息
     */
    fetchEnv() {
      getEnv().then((result) => {
        Object.assign(this.env, result);
      });
    },
  },
});
