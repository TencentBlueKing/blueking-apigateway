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
 * @file main entry
 * @author
 */

import './public-path'
import Vue from 'vue'
import '@/common/bkmagic'
import App from '@/App'
import router from '@/router'
import store from '@/store'
import VueClipboard from 'vue-clipboard2'
import { injectCSRFTokenToHeaders } from '@/api'
import auth from '@/common/auth'
import Exception from '@/components/exception'
import { bus } from '@/common/bus'
import AuthComponent from '@/components/auth'
import AgLoader from '@/components/loader'
import apiGwUI from '@/components/ui'
import preload from '@/common/preload'
import preloadDoc from '@/common/preload-doc'
import tableEmpty from '@/components/ui/table-empty'
import roundLoading from '@/components/round-loading'
import breadcrumbItem from '@/components/breadcrumb/breadcrumb-item'

// 全量引入自定义图标
import './assets/iconfont/style.css'
import globalConfig from '../static/json/config.js'
import i18n from '@/language/i18n'
import { renderHeader } from '@/common/util.js'
import SideNav from '@/components/side-nav'

Vue.use(apiGwUI)
Vue.use(VueClipboard)
Vue.component('app-exception', Exception)
Vue.component('app-auth', AuthComponent)
Vue.component('ag-loader', AgLoader)
Vue.component('table-empty', tableEmpty)
Vue.component('round-loading', roundLoading)
Vue.component('side-nav', SideNav)
Vue.component('bk-breadcrumb-item', breadcrumbItem)

// 注入全局变量
window.GLOBAL_CONFIG = globalConfig
if (!Vue.prototype.GLOBAL_CONFIG) {
  Vue.prototype.GLOBAL_CONFIG = {
    ...globalConfig,
    PLATFORM_FEATURE: {}
  }
} else {
  Vue.prototype.GLOBAL_CONFIG = {
    ...Vue.prototype.GLOBAL_CONFIG,
    ...globalConfig
  }
}
Vue.prototype.$renderHeader = renderHeader
document.title = i18n.t('API Gateway | 腾讯蓝鲸智云')
auth.requestCurrentUser().then(async (user) => {
  injectCSRFTokenToHeaders()
  if (user.isAuthenticated) {
    global.bus = bus
    await preloadDoc(Vue)
    await preload(Vue)
    global.mainComponent = new Vue({
      el: '#app',
      router,
      store,
      i18n,
      components: { App },
      mounted () {
        // alert(window.innerWidth)
      },
      template: '<App/>'
    })
  } else {
    auth.redirectToLogin()
  }
}, _ => {
  auth.redirectToLogin()
})
