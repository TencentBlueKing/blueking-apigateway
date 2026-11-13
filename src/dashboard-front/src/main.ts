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
// 引入 iconcool / bk-icon-font 样式（SVG 雪碧图 iconcool.js 在文件末尾异步加载）
import './assets/bk_icon_font/style.css';

// 全量引入 bkui-vue
import bkui from 'bkui-vue';
// 全量引入 bkui-vue 样式
import 'bkui-vue/dist/style.css';
// 全局通知组件样式
import '@blueking/notice-component/dist/style.css';
// UnoCSS
import 'virtual:uno.css';
import '@unocss/reset/tailwind-compat.css';

import i18n from './locales';
import { BkXssFilterDirective } from '@blueking/xss-filter';

import directive from '@/directives';
import AgIcon from '@/components/base/ag-icon/Index.vue';
import AgIconButton from '@/components/base/ag-icon-button/Index.vue';
import AgCopyButton from '@/components/base/ag-copy-button/Index.vue';
//  highlight.js github代码高亮风格
import 'highlight.js/styles/github.css';
// 多租户组件样式
import '@blueking/bk-user-selector/vue3/vue3.css';

const app = createApp(App);

app.use(createPinia())
  .use(router)
  .use(bkui)
  .use(i18n)
  .use(BkXssFilterDirective)
  .use(directive)
  // 全局组件
  .component('AgIcon', AgIcon)
  .component('AgIconButton', AgIconButton)
  .component('AgCopyButton', AgCopyButton);

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

// iconcool 的 SVG 雪碧图约 84 KB（gzip），只有 AgIcon 的 svg 模式、插件图标等少数地方用到，
// 空闲时再加载，不占首屏。加载后插入 body，已渲染的 <use> 引用会自动显示。
// 加载失败时记录错误，刷新页面后重新加载。
const loadIconSprite = () => import('./assets/bk_icon_font/iconcool.js').catch((error) => {
  console.error('SVG 图标雪碧图加载失败', error);
});
if (typeof window.requestIdleCallback === 'function') {
  window.requestIdleCallback(loadIconSprite, { timeout: 2000 });
}
else {
  setTimeout(loadIconSprite, 0);
}
