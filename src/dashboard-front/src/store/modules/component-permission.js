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
    permissionApplyCount: 0
  },
  mutations: {
    updatePermissionApplyList (state, data) {
      state.permissionApplyCount = data.count
    }
  },
  actions: {
    getPermissions (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/app-permissions/?${json2Query(params)}`
      return http.get(url, {}, config)
    },

    getPermissionRecord (context, { id }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/apply-records/${id}/`
      return http.get(url, {}, config)
    },

    getPermissionByHandled (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/apply-records/handled/?${json2Query(params)}`
      return http.get(url, {}, config)
    },

    getPermissionByPending (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/apply-records/pending/?${json2Query(params)}`
      return http.get(url, {}, config).then(res => {
        context.commit('updatePermissionApplyList', res.data)
        return res
      })
    },

    permRenew (context, data, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/app-permissions/renew/`
      return http.post(url, data, config)
    },

    permApproval (context, data, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/apply-records/handle/`
      return http.post(url, data, config)
    },

    permDelete (context, data, config = {}) {
      const url = `${DASHBOARD_URL}/esb/permissions/app-permissions/delete/`
      return http.post(url, data, config)
    }
  }
}
