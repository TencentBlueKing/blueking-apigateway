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
var APP_VERSION = 'ee'
var BK_LOGIN_SIGN_IN_URL = process.env.BK_LOGIN_SIGN_IN_URL || <%=BK_LOGIN_SIGN_IN_URL%> // 登录跳转地址
var API_RESOURCE_URL_TMPL = process.env.API_RESOURCE_URL_TMPL || <%=API_RESOURCE_URL_TMPL%> // 环境访问配置格式
var FEED_BACK_LINK = process.env.FEED_BACK_LINK || <%=FEED_BACK_LINK%> // 反馈地址
var BK_DOCS_URL_PREFIX = process.env.BK_DOCS_URL_PREFIX || <%=BK_DOCS_URL_PREFIX%> // 文档地址前缀
var DASHBOARD_URL = process.env.DASHBOARD_URL || <%=DASHBOARD_URL%> // 模块 Dashboard 服务地址
var DASHBOARD_CSRF_COOKIE_NAME = process.env.DASHBOARD_CSRF_COOKIE_NAME || <%=DASHBOARD_CSRF_COOKIE_NAME%> // 后端公共csrf cookie名称
var BK_TEST_APP_CODE = process.env.DEFAULT_TEST_APP_CODE || process.env.BK_APP_CODE || 'apigw-api-test' // API网关的测试应用

var BK_COMPONENT_API_URL = process.env.BK_COMPONENT_API_URL || <%=BK_COMPONENT_API_URL%> // 蓝鲸组件API地址，目前值跟 v2 开发者中心一致，内部版本不用填
var LIST_USERS_API_URL = `${BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fs_list_users/` // 人员选择器接口地址，可选填
var BK_PAAS2_ESB_URL = process.env.BK_PAAS2_ESB_URL || <%=BK_PAAS2_ESB_URL%>
var DOCS_URL_PREFIX = `${BK_DOCS_URL_PREFIX}/markdown/APIGateway`
var VERSION = process.env.BK_APIGATEWAY_VERSION || <%=BK_APIGATEWAY_VERSION%> || '1.1.1'

var DASHBOARD_FE_URL = process.env.DASHBOARD_FE_URL || <%=DASHBOARD_FE_URL%>
var BK_PAAS2_ESB_DOC_URL = process.env.BK_PAAS2_ESB_DOC_URL || <%=BK_PAAS2_ESB_DOC_URL%>
