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
    resourceList: [],
    labelName: '',
    methodName: ''
  },
  mutations: {
    setLabelName (state, data) {
      state.labelName = data
    },
    setmethodName (state, data) {
      state.methodName = data
    }
  },
  actions: {
    getApigwResources (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },

    getApigwResourceAddr (context, { apigwId, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/${resourceId}/urls/`
      return http.get(url, {}, config)
    },

    addApigwResource (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/`
      return http.post(url, data, config)
    },

    getApigwResourceDetail (context, { apigwId, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/${resourceId}/`
      return http.get(url, {}, config)
    },

    getApigwResourceDoc (context, { apigwId, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/${resourceId}/docs/`
      return http.get(url, {}, config)
    },

    saveApigwResourceDoc (context, { apigwId, resourceId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/${resourceId}/docs/`
      return http.post(url, data, config)
    },
    updateApigwResourceDoc (context, { apigwId, resourceId, data, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/${resourceId}/docs/${id}/`
      return http.put(url, data, config)
    },

    deleteApigwResourceDoc (context, { apigwId, resourceId, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/${resourceId}/docs/${id}/`
      return http.delete(url, config)
    },

    updateApigwResource (context, { apigwId, resourceId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/${resourceId}/`
      return http.put(url, data, config)
    },

    updateApigwResourceStatus (context, { apigwId, resourceId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/${resourceId}/status/`
      return http.put(url, data, config)
    },

    deleteApigwResource (context, { apigwId, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/${resourceId}/`
      return http.delete(url, {}, config)
    },

    batchDeleteApigwResource (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/batch/`
      return http.delete(url, { data }, config)
    },

    batchEditApigwResource (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/batch/`
      return http.put(url, data, config)
    },

    checkApigwResourcePath (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/proxy_paths/?${json2Query(data)}`
      return http.get(url, data, config)
    },

    checkNeedNewVersion (context, { apigwId, useGlobalMessage }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/need_new_version/`
      return http.get(url, { useGlobalMessage })
    },

    getStageBaseInfo (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/basic/?${json2Query(pageParams)}`
      return http.get(url, config)
    },

    getResourceStages (context, { apigwId, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/${resourceId}/stages/`
      return http.get(url, config)
    },

    getReleaseResource (context, { apigwId, versionId, resourceId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/releases/resource-versions/${versionId}/resources/${resourceId}/`
      return http.get(url, config)
    },

    exportApigwResource (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/export/`
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
    },

    exportApigwResourceDocs (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/docs/export/`
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
    },

    checkResourceImport (context, { apigwId, params }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/import/check/`
      return http.post(url, params, config)
    },

    importResource (context, { apigwId, params }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/import/`
      return http.post(url, params, config)
    },

    importSwagger (context, { apigwId, params }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/docs/import/by-swagger/`
      return http.post(url, params, config)
    },

    importArchive (context, { apigwId, params }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/resources/docs/import/by-archive/`
      return http.post(url, params, config)
    }
  }
}
