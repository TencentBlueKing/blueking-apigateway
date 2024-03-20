import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import App from './app.vue';
import i18n from './language/i18n';
import './css/index.css';
import globalConfig from '@/constant/config';
import directive from '@/directive/index';
import mavonEditor from 'mavon-editor';
import 'mavon-editor/dist/css/index.css';

// 全量引入 bkui-vue
import bkui from 'bkui-vue';
// import bkui, { bkTooltips, overflowTitle } from 'bkui-vue';
// 全量引入 bkui-vue 样式
import 'bkui-vue/dist/style.css';
// 图标
import './assets/iconfont/style.css';

const app = createApp(App);
app.config.globalProperties.GLOBAL_CONFIG = globalConfig;

app.use(i18n)
  .use(directive)
  .use(router)
  .use(createPinia())
  .use(bkui)
  // .directive('overflowTitle', overflowTitle)
  // .directive('bkTooltips', bkTooltips)
  .use(mavonEditor)
  .mount('.app');
