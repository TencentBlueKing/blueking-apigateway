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
    getApigwVersions (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/?${json2Query(pageParams)}`
      return http.get(url, config).then(res => {
        res.data.results.forEach(item => {
          item.text = `${item.title} (${item.name})`
        })
        return res
      })
    },

    getApigwVersionByStage (context, { apigwId, stageId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/releases/stages/${stageId}/`
      return http.get(url, config)
    },

    getApigwVersionByStages (context, { apigwId, stageIds }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/releases/`
      return http.post(url, { ids: stageIds }, config)
    },

    getApigwVersionLatest (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/releases/histories/latest`
      return http.get(url, config)
    },

    createApigwVersion (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/`
      return http.post(url, data, config)
    },

    updateApigwVersionDetail (context, { apigwId, versionId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/${versionId}/`
      return http.put(url, data, config)
    },

    createApigwRelease (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/releases/`
      return http.post(url, data, config)
    },

    createApigwReleases (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/releases/batch/`
      return http.post(url, data, { useGlobalMessage: false })
    },

    updateApigwVersion (context, { apigwId, versionId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/${versionId}/`
      return http.put(url, data, config)
    },

    deleteApigwVersion (context, { apigwId, versionId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/${versionId}/`
      return http.delete(url, {}, config)
    },

    getApigwVersionDetail (context, { apigwId, versionId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/${versionId}/`
      return http.get(url, config)
    },

    getVersionDiff (context, { apigwId, sourceId, targetId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/diff/?source_resource_version_id=${sourceId}&target_resource_version_id=${targetId}`
      return http.get(url, config)
    },

    getNewVersonInfo (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resource_versions/?limit=1&offset=0`
      return http.get(url, config)
    }
  }
}
