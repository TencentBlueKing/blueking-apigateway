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
 * @file main store
 * @author
 */

import Vue from 'vue'
import Vuex from 'vuex'

import apis from './modules/apis'
import label from './modules/label'
import stage from './modules/stage'
import resource from './modules/resource'
import version from './modules/version'
import release from './modules/release'
import permission from './modules/permission'
import strategy from './modules/strategy'
import options from './modules/options'
import accessLog from './modules/access-log'
import monitor from './modules/monitor'
import report from './modules/report'
import apiTest from './modules/api-test'
import sdk from './modules/sdk'
import audit from './modules/audit'
import system from './modules/system'
import docCategory from './modules/doc-category'
import category from './modules/category'
import component from './modules/components'
import runtime from './modules/runtime'
import componentPermission from './modules/component-permission'
import microGateway from './modules/micro-gateway'
import gatewayPlugin from './modules/gateway-plugin'
import apigw from './modules/apigw'
import esb from './modules/esb'
import sdkDoc from './modules/sdk-doc'
import docs from './modules/docs'
import http from '@/api'
import { unifyObjectStyle } from '@/common/util'
import MarkdownIt from 'markdown-it'
import cookie from 'cookie'

Vue.config.devtools = NODE_ENV === 'development'

Vue.use(Vuex)

const store = new Vuex.Store({
  // 模块
  modules: {
    apis,
    label,
    stage,
    version,
    resource,
    release,
    permission,
    strategy,
    options,
    accessLog,
    monitor,
    report,
    apiTest,
    sdk,
    audit,
    system,
    docCategory,
    category,
    component,
    runtime,
    componentPermission,
    microGateway,
    gatewayPlugin,
    apigw,
    esb,
    sdkDoc,
    docs
  },
  // 公共 store
  state: {
    mainContentLoading: false,
    menuOpened: true,
    platformFeature: null,
    curApigw: {},
    // 系统当前登录用户
    user: {},
    userAuthType: [],
    defaultUserAuthType: '',
    loadingConf: {
      speed: 2,
      primaryColor: '#EBECF3',
      secondaryColor: '#F6F7FB'
    },
    localLanguage: cookie.parse(document.cookie).blueking_language || 'zh-cn'
  },
  // 公共 getters
  getters: {
    mainContentLoading: state => state.mainContentLoading,
    menuOpened: state => state.menuOpened,
    user: state => state.user
  },
  // 公共 mutations
  mutations: {
    /**
         * 设置内容区的 loading 是否显示
         *
         * @param {Object} state store state
         * @param {boolean} loading 是否显示 loading
         */
    setMainContentLoading (state, loading) {
      state.mainContentLoading = loading
    },

    /**
         * 设置侧导航是否展开
         *
         * @param {Object} state store state
         * @param {boolean} opened 是否展开
         */
    setMenuOpened (state, opened) {
      state.menuOpened = opened
    },

    /**
         * 更新当前用户 user
         *
         * @param {Object} state store state
         * @param {Object} user user 对象
         */
    updateUser (state, user) {
      state.user = Object.assign({}, user)
    },

    updateCurApigw (state, data) {
      state.curApigw = data
    },

    updatePlatformFeature (state, data) {
      state.platformFeature = data
    },

    updateUserAuthType (state, data) {
      const md = new MarkdownIt()
      data.forEach(item => {
        item.description = md.render(item.description)
      })
      state.defaultUserAuthType = data[0].name
      state.userAuthType = data
    },

    switchLanguage (state, data) {
      state.localLanguage = data
    }
  },
  actions: {
    /**
         * 获取用户信息
         *
         * @param {Object} context store 上下文对象 { commit, state, dispatch }
         *
         * @return {Promise} promise 对象
         */
    userInfo (context, config = {}) {
      const url = `${DASHBOARD_URL}/accounts/userinfo/`
      return http.get(url).then(response => {
        const userData = response.data || {}
        context.commit('updateUser', userData)
        return userData
      })
    },

    getBkAppCodes (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-${pageParams.dimension === 'api' ? 'gateway' : 'resource'}-permissions/bk-app-codes/`
      return http.get(url, config)
    },

    getPlatformFeature (context, config = {}) {
      const url = `${DASHBOARD_URL}/feature/flags/`
      return http.get(url, config).then(res => {
        context.commit('updatePlatformFeature', res.data)
        return res
      })
    },

    getUserAuthType (context, config = {}) {
      const url = `${DASHBOARD_URL}/users/user_auth_types/`
      return http.get(url, config).then(res => {
        context.commit('updateUserAuthType', res.data)
        return res
      })
    },

    updateLanguage (context, data, config = {}) {
      const url = `${DASHBOARD_URL}/i18n/setlang/`
      return http.post(url, data, config)
    },

    feedback (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/docs/feedback/`
      return http.post(url, params, config)
    }
  }
})

/**
 * hack vuex dispatch, add third parameter `config` to the dispatch method
 *
 * @param {Object|string} _type vuex type
 * @param {Object} _payload vuex payload
 * @param {Object} config config 参数，主要指 http 的参数，详见 src/api/index initConfig
 *
 * @return {Promise} 执行请求的 promise
 */
store.dispatch = function (_type, _payload, config = {}) {
  const { type, payload } = unifyObjectStyle(_type, _payload)

  const action = { type, payload, config }
  const entry = store._actions[type]
  if (!entry) {
    if (NODE_ENV !== 'production') {
      console.error(`[vuex] unknown action type: ${type}`)
    }
    return
  }

  store._actionSubscribers.forEach(sub => {
    return sub(action, store.state)
  })

  return entry.length > 1
    ? Promise.all(entry.map(handler => handler(payload, config)))
    : entry[0](payload, config)
}

export default store
