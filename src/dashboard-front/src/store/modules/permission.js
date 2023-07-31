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
import cookie from 'cookie'

export default {
  namespaced: true,
  state: {
    permissionApplyCount: 0,
    permissionApplyList: []
  },
  mutations: {
    updatePermissionApplyList (state, data) {
      state.permissionApplyList = data.results
      state.permissionApplyCount = data.count
    }
  },
  actions: {
    getApigwPermissionList (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-${pageParams.dimension === 'api' ? 'gateway' : 'resource'}-permissions/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },

    getApigwPermissionApplyList (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-apply/?${json2Query(pageParams)}`
      return http.get(url, {}, config).then((res) => {
        context.commit('updatePermissionApplyList', res.data)
        return res
      })
    },

    getApigwPermissionRecordList (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-records/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },

    addApigwPermissionApply (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-${data.dimension === 'api' ? 'gateway' : 'resource'}-permissions/`
      return http.post(url, data, config)
    },

    updateApigwPermissionStatus (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-permission-apply/approval/`
      return http.post(url, data, config)
    },

    batchUpdateApigwPermission (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-${data.dimension === 'api' ? 'gateway' : 'resource'}-permissions/renew/`
      return http.post(url, data, config)
    },

    deleteApigwPermission (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-${data.dimension === 'api' ? 'gateway' : 'resource'}-permissions/delete/`
      return http.post(url, data, config)
    },

    exportApigwPermission (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/gateways/${apigwId}/permissions/app-${data.dimension === 'api' ? 'gateway' : 'resource'}-permissions/export/`
      const CSRFToken = cookie.parse(document.cookie)[DASHBOARD_CSRF_COOKIE_NAME || `${window.PROJECT_CONFIG.BKPAAS_APP_ID}_csrftoken`]
      return fetch(url, {
        credentials: 'include',
        method: 'POST',
        body: JSON.stringify(data),
        headers: new Headers({
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRFToken
        })
      })
    }
  }
}
