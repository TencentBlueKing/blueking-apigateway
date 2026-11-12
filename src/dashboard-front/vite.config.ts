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
export default defineConfig(({ mode, command }) => {
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
      // 仅开发时启用：生产构建下它的功能全部关闭，但仍会逐个解析源文件，白白拖慢构建
      command === 'serve' && TurboConsole({}),
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
      rolldownOptions: {
        input: {
          main: path.resolve(import.meta.dirname, 'index.html'),
          default: path.resolve(import.meta.dirname, 'default.html'),
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
