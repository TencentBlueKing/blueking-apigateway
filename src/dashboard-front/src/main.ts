/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

// 全量引入 bkui-vue
import bkui from 'bkui-vue';
// 全量引入 bkui-vue 样式
import '../node_modules/bkui-vue/dist/style.variable.css';
// UnoCSS
import 'virtual:uno.css';
import '@unocss/reset/tailwind-compat.css';

import i18n from './locales';
import VueDOMPurifyHTML from 'vue-dompurify-html';

import directive from '@/directives';
import AgIcon from '@/components/ag-icon/Index.vue';
import IconButton from '@/components/icon-button/Index.vue';
import CopyButton from '@/components/copy-button/Index.vue';
import CardContainer from '@/components/card-container/Index.vue';
import mavonEditor from 'mavon-editor';
import 'mavon-editor/dist/css/index.css';
// highlight.js 代码高亮风格
import 'highlight.js/styles/vs2015.min.css';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(bkui);
app.use(i18n);
app.use(mavonEditor);
app.use(VueDOMPurifyHTML);
app.use(directive);

// 全局组件
app.component('AgIcon', AgIcon)
  .component('IconButton', IconButton)
  .component('CopyButton', CopyButton)
  .component('CardContainer', CardContainer);

app.mount('#app');
