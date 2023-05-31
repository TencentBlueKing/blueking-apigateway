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
/**
 * @file prod server
 * 静态资源
 * 模块渲染输出
 * 注入全局变量
 * 添加html模板引擎
 */
import express from 'express'
import path from 'path'
import fs from 'fs'
import artTemplate from 'express-art-template'
import history from 'connect-history-api-fallback'
import cookieParser from 'cookie-parser'
import axios from 'axios'
import ajaxMiddleware from './ajax-middleware'
import config from './config'

const app = new express()
const PORT = process.env.PORT || config.build.localDevPort || 5000
const http = axios.create({
	withCredentials: true
})

http.interceptors.response.use(response => response, error => Promise.reject(error))

// 注入全局变量
const GLOBAL_VAR = {
    SITE_URL: '',
	BK_STATIC_URL: '',
    REMOTE_STATIC_URL: process.env.BKPAAS_REMOTE_STATIC_URL || '',
	// APP CODE
	BKPAAS_APP_ID: process.env.BKPAAS_APP_ID || '',
	// node process env，用于注入window对象
    NODE_ENV: process.env.NODE_ENV || '',
    BKPAAS_ENVIRONMENT: process.env.BKPAAS_ENVIRONMENT || '',
    PORT: process.env.PORT || '',
    API_RESOURCE_URL_TMPL: process.env.API_RESOURCE_URL_TMPL || '',
    FEED_BACK_LINK: process.env.FEED_BACK_LINK || '',
    BK_DOCS_URL_PREFIX: process.env.BK_DOCS_URL_PREFIX || '',
    DASHBOARD_URL: process.env.DASHBOARD_URL || '',
    DASHBOARD_CSRF_COOKIE_NAME: process.env.DASHBOARD_CSRF_COOKIE_NAME || '',
    DEFAULT_TEST_APP_CODE: process.env.DEFAULT_TEST_APP_CODE || '',
    BK_COMPONENT_API_URL: process.env.BK_COMPONENT_API_URL || '',
    BK_PAAS2_ESB_URL: process.env.BK_PAAS2_ESB_URL || '',
    BK_APIGATEWAY_VERSION: process.env.BK_APIGATEWAY_VERSION || '',
    BK_LOGIN_SIGN_IN_URL: process.env.BK_LOGIN_SIGN_IN_URL || '',
    APP_VERSION: process.env.APP_VERSION || '',
    BK_APP_CODE: process.env.BK_APP_CODE || '',
    npm_config_report: process.env.npm_config_report || '',
    DASHBOARD_FE_URL: process.env.DASHBOARD_FE_URL || '',
    BK_PAAS2_ESB_DOC_URL: process.env.BK_PAAS2_ESB_DOC_URL || '',
	NODE_PROCESS_ENV: JSON.stringify(process.env)
}

// APA 重定向回首页，由首页Route响应处理
// https://github.com/bripkens/connect-history-api-fallback#index
app.use(history({
	index: '/',
	rewrites: [
        {
            // connect-history-api-fallback 默认会对 url 中有 . 的 url 当成静态资源处理而不是当成页面地址来处理
            // 兼容 /cs/28aa9eda67644a6eb254d694d944307e/cluster/BCS-MESOS-10001/node/1.121.23.12 这样以 IP 结尾的 url
            // from: /\d+\.\d+\.\d+\.\d+$/,
            from: /\/(\d+\.)*\d+$/,
            to: '/'
        },
        {
            // connect-history-api-fallback 默认会对 url 中有 . 的 url 当成静态资源处理而不是当成页面地址来处理
            // 兼容 /bcs/projectId/app/214/taskgroups/0.application-1-13.test123.10013.1510806131114508229/containers/containerId
            from: /\/\/+.*\..*\//,
            to: '/'
        },
        {
        	from: '/user',
        	to: '/user'
        }
    ]
}))

app.use(cookieParser())

// 首页
app.get('/', (req, res) => {
	const index = path.join(__dirname, '../dist/index.html')
	res.render(index, GLOBAL_VAR)
})

app.use(ajaxMiddleware)
// 配置静态资源
app.use('/static', express.static(path.join(__dirname, '../dist/static')))

// 配置视图
app.set('views', path.join(__dirname, '../dist'))

// 配置模板引擎
// http://aui.github.io/art-template/zh-cn/docs/
app.engine('html', artTemplate)
app.set('view engine', 'html')

// 配置端口
app.listen(PORT, () => {
	console.log(`App is running in port ${PORT}`)
})
