import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router';
import 'virtual:uno.css';
import '@unocss/reset/normalize.css';

// 全量引入 bkui-vue
import bkui from 'bkui-vue';
// 全量引入 bkui-vue 样式
import '../node_modules/bkui-vue/dist/style.variable.css';
// icon font
import '@/lib/bk_icon_font/style.css';

import i18n from './locales';
import VueDOMPurifyHTML from 'vue-dompurify-html';

import directive from '@/directives';

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(bkui);
app.use(i18n);
app.use(VueDOMPurifyHTML);
app.use(directive);

app.mount('#app');
