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
 * @file 页面公共请求即每切换 router 时都必须要发送的请求
 * @author
 */

import store from '@/store'

/**
 * 获取平台Feature
 */
function getPlatformFeature (Vue) {
  // 注入全局配置
  if (!Vue.prototype.GLOBAL_CONFIG) {
    Vue.prototype.GLOBAL_CONFIG = {
      PLATFORM_FEATURE: {}
    }
  }
  if (store.state.platformFeature) {
    const platformFeature = store.state.platformFeature
    Vue.prototype.GLOBAL_CONFIG.PLATFORM_FEATURE = { ...platformFeature }
    return platformFeature
  }
  const promise = new Promise(async function (resolve, reject) {
    const res = await store.dispatch('getPlatformFeature')
    Vue.prototype.GLOBAL_CONFIG.PLATFORM_FEATURE = { ...res.data }
    resolve(res)
  })
  return promise
}

export default function (Vue) {
  return Promise.all([
    getPlatformFeature(Vue)
  ])
}
