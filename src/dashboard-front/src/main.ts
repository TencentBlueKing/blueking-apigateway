/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router';
import './styles/index.scss';
// 引入 iconcool / bk-icon-font 样式
import './assets/bk_icon_font/style.css';
import './assets/bk_icon_font/iconcool.js';

// 全量引入 bkui-vue
import bkui from 'bkui-vue';
// 全量引入 bkui-vue 样式
import 'bkui-vue/dist/style.css';
// 全局通知组件样式
import '@blueking/notice-component/dist/style.css';
// 版本发布通知组件样式
import '@blueking/release-note/vue3/vue3.css';
// UnoCSS
import 'virtual:uno.css';
import '@unocss/reset/tailwind-compat.css';

import i18n from './locales';
import { BkXssFilterDirective } from '@blueking/xss-filter';

import directive from '@/directives';
import AgIcon from '@/components/ag-icon/Index.vue';
import IconButton from '@/components/icon-button/Index.vue';
import CopyButton from '@/components/copy-button/Index.vue';
import CardContainer from '@/components/card-container/Index.vue';
import mavonEditor from 'mavon-editor';
import 'mavon-editor/dist/css/index.css';
//  highlight.js github代码高亮风格
import 'highlight.js/styles/github.css';
// 多租户组件样式
import '@blueking/bk-user-selector/vue3/vue3.css';
// status tag 业务组件
import('@blueking/status-tag');

const app = createApp(App);

app.use(createPinia())
  .use(router)
  .use(bkui)
  .use(i18n)
  .use(mavonEditor)
  .use(BkXssFilterDirective)
  .use(directive)
  // 全局组件
  .component('AgIcon', AgIcon)
  .component('IconButton', IconButton)
  .component('CopyButton', CopyButton)
  .component('CardContainer', CardContainer);

// 等首次导航完成后再挂载：否则挂载时 currentRoute 仍是初始 location，
// 依赖当前路由信息的逻辑（如 use-table-setting 的表格列缓存标识）会取到空值。
// 超时兜底：isReady 只在 resolve/reject 后 settle，若守卫内请求异常挂起会阻塞挂载，
// 超过阈值则先挂载外壳（内容区仍由 App.vue 的 userLoaded 门控，路由就绪后状态会响应式补齐）。
const ROUTER_READY_TIMEOUT = 10_000;

Promise.race([
  router.isReady().catch(() => undefined),
  new Promise<void>((resolve) => {
    setTimeout(resolve, ROUTER_READY_TIMEOUT);
  }),
]).then(() => {
  app.mount('#app');
});
