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
import http from '@/api'
// import queryString from 'query-string'

export default {
  namespaced: true,
  state: {
  },
  mutations: {
  },
  actions: {
    getComponentAPI (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/systems/`
      return http.get(url, config)
    },

    searchAPI (context, { version, keyword }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/${version}/components/search/?query=${keyword}`
      return http.get(url, config)
    },

    getSystemDetail (context, { version, systemName }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/${version}/systems/${systemName}/`
      return http.get(url, config)
    },

    getSystemComponents (context, { version, systemName }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/${version}/systems/${systemName}/components/`
      return http.get(url, config)
    },

    getSystemComponentDoc (context, { version, systemName, componentId }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/${version}/systems/${systemName}/components/${componentId}/doc/`
      return http.get(url, config)
    },

    getSDKDetail (context, { version, language }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/${version}/sdks/latest/?language=${language}`
      return http.get(url, config)
    },

    getSDKDoc (context, { version, language, systemName, componentId }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/esb/${version}/systems/${systemName}/components/${componentId}/sdks/usage-example/?language=${language}`
      return http.get(url, config)
    }
  }
}
