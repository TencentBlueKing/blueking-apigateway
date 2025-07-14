import {
  URL,
  fileURLToPath,
} from 'node:url';

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import vueDevTools from 'vite-plugin-vue-devtools';
import AutoImport from 'unplugin-auto-import/vite';
import UnoCSS from 'unocss/vite';
import TurboConsole from 'unplugin-turbo-console/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: 'dev-t.paas3-dev.bktencent.com',
    port: 8888,
    strictPort: true,
    // https: true,
    open: true,
  },
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 多租户名称展示标签不要解析为组件
          isCustomElement: tag => tag === 'bk-user-display-name',
        },
      },
    }),
    vueJsx(),
    vueDevTools(),
    AutoImport({
      imports: [
        'vue',
        'vue-router',
        {
          'vue-i18n': [
            'useI18n',
          ],
        },
      ],
      dts: './src/types/auto-imports.d.ts',
      viteOptimizeDeps: true,
    }),
    UnoCSS(),
    TurboConsole({}),
    basicSsl(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'bkui-vue': 'bkui-vue/dist/index.esm.js',
      'bkui-lib': 'bkui-vue/lib',
    },
  },
});
