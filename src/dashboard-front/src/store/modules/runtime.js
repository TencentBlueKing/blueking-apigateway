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

export default {
  namespaced: true,
  state: {
  },
  mutations: {
  },
  actions: {
    getApigwRuntime (context, { timeRange }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/status/systems/summary/?time_since=${timeRange}`
      return http.get(url)
    },

    getApigwSystemSummary (context, { system, start, end }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/status/systems/${system}/summary/?time_since=custom&mts_start=${start}&mts_end=${end}`
      return http.get(url)
    },

    getApigwTimeline (context, { apigwId, params }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/status/systems/events/timeline/`
      return http.get(url)
    },

    getApigwChartDetail (context, { system, start, end }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/status/systems/${system}/date_histogram/?time_interval=1m&mts_start=${start}&mts_end=${end}`
      return http.get(url)
    },

    getApigwRuntimeRequest (context, { type, system, start, end }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/status/systems/${system}/details/group_by/?time_since=custom&mts_start=${start}&mts_end=${end}&group_by=${type}&order=availability_asc`
      return http.get(url)
    },

    getApigwErrorRequest (context, { system, appCode, requestUrl, componentName, start, end }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/status/systems/${system}/errors/?url=${requestUrl}&app_code=${appCode}&component_name=${componentName}&mts_start=${start}&mts_end=${end}&size=200`
      return http.get(url)
    }
  }
}
