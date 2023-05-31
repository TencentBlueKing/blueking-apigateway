/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import Vue from 'vue';
import i18n from '@/language/i18n';

const staticI18n = new Vue({
    i18n
})

module.exports = {
    // 登录
    LOGIN_URL: BK_LOGIN_SIGN_IN_URL,

    // 助手
    HELPER: {
        name: '',
        href: '',
    },

    // 底部信息
    FOOT_INFO: {
        NAME: staticI18n.$t('技术支持'),
        NAMEHREF: 'https://wpa1.qq.com/KziXGWJs?_type=wpa&qidian=true',
        COMMUNITY: staticI18n.$t('社区论坛'),
        COMMUNITYHREF: 'https://bk.tencent.com/s-mart/community/',
        PRODUCT: staticI18n.$t('产品官网'),
        PRODUCTHREF: 'https://bk.tencent.com/index/',
        VERSION: VERSION
    },

    // 人员列表接口地址，外部版本必填
    USERS_LIST_URL: LIST_USERS_API_URL,

    // 问题反馈
    FEED_BACK_LINK: FEED_BACK_LINK,

    // 环境访问地址域名
    STAGE_DOMAIN: API_RESOURCE_URL_TMPL,

    // 加入圈子
    MARKER: '',

    OA_DOMAIN: '',

    WOA_DOMAIN: '',

    IED_DOMAIN: '',

    // 网关管理
    APIGW: DASHBOARD_FE_URL,

    // 旧版地址
    OLD_SITE_URL: '',

    // 常用工具
    TOOLS: '',

    // createChat api
    CREATE_CHAT_API: '',

    // sendChat api
    SEND_CHAT_API: '',

    PREV_URL: '/docs',

    DOC: {
        // 使用指南
        GUIDE: `${DOCS_URL_PREFIX}`,

        // “请求流水查询规则”
        QUERY_USE: `${DOCS_URL_PREFIX}/apigateway/reference/log-search-specification.md`,

        // 蓝鲸用户认证
        USER_VERIFY: `${DOCS_URL_PREFIX}/apigateway/use-api/bk-user.md`,

        // API资源模板变量
        TEMPLATE_VARS: `${DOCS_URL_PREFIX}/apigateway/reference/template-vars.md`,

        // 网关认证
        AUTH: `${DOCS_URL_PREFIX}/apigateway/reference/authorization.md`,

        // Swagger说明文档
        SWAGGER: `${DOCS_URL_PREFIX}/apigateway/reference/swagger.md`,

        // 跨域资源共享(CORS)
        CORS: `${DOCS_URL_PREFIX}/apigateway/plugins/cors.md`,

        // 断路器
        BREAKER: `${DOCS_URL_PREFIX}/apigateway/plugins/circuit-breaker.md`,

        // 频率控制
        RATELIMIT: `${DOCS_URL_PREFIX}/apigateway/plugins/rate-limit.md`,

        // JWT
        JWT: `${DOCS_URL_PREFIX}/apigateway/reference/authorization.md`,

        // 用户类型
        USER_TYPE: `${DOCS_URL_PREFIX}/apigateway/reference/user-type.md`,

        // API网关错误码
        ERROR_CODE: `${DOCS_URL_PREFIX}/apigateway/faq/error-codes.md`,

        // 组件频率控制
        COMPONENT_RATE_LIMIT: `${DOCS_URL_PREFIX}/component/reference/rate-limit.md`,

        // 如何开发和发布组件
        COMPONENT_CREATE_API: `${DOCS_URL_PREFIX}/component/quickstart/create-api.md`,

        //文档导入详情
        IMPORT_RESOURCE_DOCS: `${DOCS_URL_PREFIX}/apigateway/howto/import-resource-docs.md`,

        //实例类型
        INSTANCE_TYPE: `${DOCS_URL_PREFIX}/`,

        // 调用API
        USER_API: DOCS_URL_PREFIX + '/apigateway/use-api/use-apigw-api.md'
    }
}
