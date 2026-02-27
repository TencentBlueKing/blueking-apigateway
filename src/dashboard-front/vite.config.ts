import { URL, fileURLToPath } from 'node:url';
import path from 'path';

import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import vueDevTools from 'vite-plugin-vue-devtools';
import AutoImport from 'unplugin-auto-import/vite';
import UnoCSS from 'unocss/vite';
import TurboConsole from 'unplugin-turbo-console/vite';
import basicSsl from '@vitejs/plugin-basic-ssl';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  return {
    server: {
      host: env.VITE_DEV_SERVER_HOST,
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
          { 'vue-i18n': ['useI18n'] },
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
        // 'bkui-vue': 'bkui-vue/dist/index.esm.js',
        'bkui-lib': 'bkui-vue/lib',
      },
    },
    build: {
      manifest: true,
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, 'index.html'),
          default: path.resolve(__dirname, 'default.html'),
        },
      },
    },
    experimental: {
      renderBuiltUrl(filename, { hostType }) {
        if (hostType === 'js') {
          return { runtime: `window.__loadAssetsUrl__(${JSON.stringify(filename)})` };
        }
        else {
          return { relative: true };
        }
      },
    },
  };
});
