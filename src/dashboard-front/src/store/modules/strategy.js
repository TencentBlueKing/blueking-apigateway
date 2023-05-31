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
 * @file api store
 * @author
 */

import http from '@/api'
import { json2Query } from '@/common/util.js'

export default {
  namespaced: true,
  state: {
  },
  mutations: {
  },
  actions: {
    getApigwStrategies (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },

    addApigwStrategy (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/`
      return http.post(url, data, config)
    },

    getApigwStrategyDetail (context, { apigwId, strategyId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/`
      return http.get(url, {}, config)
    },

    updateApigwStrategy (context, { apigwId, strategyId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/`
      return http.put(url, data, config)
    },

    deleteApigwStrategy (context, { apigwId, strategyId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/`
      return http.delete(url, {}, config)
    },

    getApigwIPGroups (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/ip_groups/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },

    addApigwIPGroup (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/ip_groups/`
      return http.post(url, data, config)
    },

    getApigwIPGroupDetail (context, { apigwId, IPGroupId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/ip_groups/${IPGroupId}/`
      return http.get(url, {}, config)
    },

    updateApigwIPGroup (context, { apigwId, IPGroupId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/ip_groups/${IPGroupId}/`
      return http.put(url, data, config)
    },

    deleteApigwIPGroup (context, { apigwId, IPGroupId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/ip_groups/${IPGroupId}/`
      return http.delete(url, {}, config)
    },

    getApigwStrategyBindings (context, { apigwId, strategyId, scopeType, type }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/bindings/?scope_type=${scopeType}&type=${type}&no_page=true`
      return http.get(url, {}, config)
    },

    updateApigwStrategyBindings (context, { apigwId, strategyId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/bindings/`
      return http.post(url, data, config)
    },

    deleteApigwStrategyBindings (context, { apigwId, strategyId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/bindings/`
      return http.delete(url, { data }, config)
    },

    checkApigwStrategyBindings (context, { apigwId, strategyId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/access_strategies/${strategyId}/bindings/diff/`
      return http.post(url, data, config)
    }
  }
}
