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
import { json2Query } from '@/common/util.js'

export default {
  namespaced: true,
  state: {
    resourceList: [],
    curApigw: {},
    curStage: ''
  },
  mutations: {
    updateCurApigw (state, data) {
      state.curApigw = data
    },
    updateApigwResources (state, data) {
      state.resourceList = data
    },
    updateCurStage (state, data) {
      state.curStage = data
    }
  },
  actions: {
    getApigwAPI (context, { pageParams }, config = {}) {
      const params = json2Query(pageParams)
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/?${params}`
      return http.get(url, config)
    },

    getApigwAPIDetail (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/${apigwId}/`
      return http.get(url, config).then(res => {
        context.commit('updateCurApigw', res.data)
        return res
      })
    },

    getApigwStages (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/${apigwId}/stages/`
      return http.get(url, config)
    },

    getApigwResources (context, { apigwId, stage }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/${apigwId}/stages/${stage}/resources/`
      return http.get(url, config).then(res => {
        context.commit('updateApigwResources', res.data.results)
        return res
      })
    },

    getApigwResourceDoc (context, { apigwId, stage, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/${apigwId}/stages/${stage}/resources/${resourceId}/doc/`
      return http.get(url, config)
    },

    getApigwResourceSDK (context, { apigwId, stage, resourceId, sdk }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/${apigwId}/stages/${stage}/resources/${resourceId}/sdks/usage-example/?language=python`
      return http.get(url, config)
    },

    getApigwSDK (context, { apigwId, language }, config = {}) {
      const url = `${DASHBOARD_URL}/docs/apigateway/apis/${apigwId}/sdks/?language=${language}`
      return http.get(url, config)
    }
  }
}
