import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router';
import 'virtual:uno.css';
import '@unocss/reset/normalize.css';
import './styles/index.scss';

// 全量引入 bkui-vue
import bkui from 'bkui-vue';
// 全量引入 bkui-vue 样式
import '../node_modules/bkui-vue/dist/style.variable.css';
// icon font
import '@/lib/bk_icon_font/style.css';

import i18n from './locales';
import VueDOMPurifyHTML from 'vue-dompurify-html';

import directive from '@/directives';
import AgIcon from '@/components/ag-icon/Index.vue';
import IconButton from '@/components/icon-button/Index.vue';
import CopyButton from '@/components/copy-button/Index.vue';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(bkui);
app.use(i18n);
app.use(VueDOMPurifyHTML);
app.use(directive);

// 全局组件
app.component('AgIcon', AgIcon)
  .component('IconButton', IconButton)
  .component('CopyButton', CopyButton);

app.mount('#app');
