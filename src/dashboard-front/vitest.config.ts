/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import { URL, fileURLToPath } from 'node:url';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import AutoImport from 'unplugin-auto-import/vite';
import { configDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  define: {
    __APP_BUILD_ID__: JSON.stringify('test'),
  },
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 与 vite.config.ts 保持一致：多租户名称展示标签不作为 Vue 组件解析
          isCustomElement: tag => tag === 'bk-user-display-name',
        },
      },
    }),
    vueJsx(),
    AutoImport({
      imports: [
        'vue',
        'vue-router',
        { 'vue-i18n': ['useI18n'] },
      ],
      // 测试环境不改写类型声明文件，避免产生无关改动
      dts: false,
    }),
  ],
  resolve: {
    alias: [
      {
        find: '@',
        replacement: fileURLToPath(new URL('./src', import.meta.url)),
      },
      {
        find: 'bkui-lib',
        replacement: 'bkui-vue/lib',
      },
      // bkui-vue 仅声明 package.json#module 缺少 main/exports，Vitest 需显式指向 ESM 入口
      {
        find: /^bkui-vue$/,
        replacement: 'bkui-vue/lib/index.js',
      },
    ],
  },
  test: {
    // 默认提供轻量级浏览器全局对象（window、localStorage 等），纯 Node 用例可按需用 @vitest-environment node 覆盖
    environment: 'happy-dom',
    root: fileURLToPath(new URL('./', import.meta.url)),
    server: {
      deps: {
        // 让依赖 bkui-vue 的蓝鲸系包统一走 Vite 管线解析别名与样式
        inline: ['bkui-vue', /^@blueking\//],
      },
    },
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: [
      ...configDefaults.exclude,
      // 保留既有手写无头浏览器回归脚本，后续阶段再迁移至 Vitest Browser Mode
      'tests/ag-table/**',
    ],
    clearMocks: true,
    restoreMocks: true,
    coverage: {
      provider: 'v8',
      reporter: [
        'text',
        'html',
        'lcov',
      ],
      reportsDirectory: './coverage',
      // 遵循 Vitest 默认行为仅统计已执行到的源码文件；后续需要全量统计时再按模块逐步配置 include
      exclude: [
        'src/**/*.d.ts',
        'src/**/__tests__/**',
        'src/**/*.{test,spec}.{ts,tsx}',
        'src/types/**',
        'src/locales/**',
        'src/images/**',
      ],
    },
  },
});
