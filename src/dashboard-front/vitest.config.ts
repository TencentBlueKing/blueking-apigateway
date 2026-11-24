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

import { existsSync } from 'node:fs';
import path from 'node:path';
import { URL, fileURLToPath } from 'node:url';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import { playwright } from '@vitest/browser-playwright';
import { chromium } from 'playwright';
import AutoImport from 'unplugin-auto-import/vite';
import { configDefaults, defineConfig } from 'vitest/config';

const rootDir = fileURLToPath(new URL('./', import.meta.url));

/**
 * 解析无头 Chromium 可执行文件路径：
 * 1. 优先尊重显式环境变量 CHROME_BIN
 * 2. 若 Playwright 管理的 Chromium 已安装，使用其默认路径（返回 undefined）
 * 3. 否则自动回退到本机已安装的 Chrome / Chromium，免去本地重复下载
 */
const resolveBrowserExecutable = (): string | undefined => {
  if (process.env.CHROME_BIN) {
    return process.env.CHROME_BIN;
  }

  try {
    const playwrightBinary = chromium.executablePath();
    if (playwrightBinary && existsSync(playwrightBinary)) {
      return undefined;
    }
  }
  catch {
    // 探测异常时继续回退到系统浏览器路径
  }

  if (process.platform === 'win32') {
    const candidates = [
      path.join(process.env.ProgramFiles || 'C:/Program Files', 'Google/Chrome/Application/chrome.exe'),
      path.join(process.env['ProgramFiles(x86)'] || 'C:/Program Files (x86)', 'Google/Chrome/Application/chrome.exe'),
    ];
    return candidates.find(candidate => existsSync(candidate));
  }

  if (process.platform === 'darwin') {
    const chromeApp = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    return existsSync(chromeApp) ? chromeApp : undefined;
  }

  const linuxCandidates = [
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ];
  return linuxCandidates.find(candidate => existsSync(candidate));
};

const browserExecutablePath = resolveBrowserExecutable();

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
    root: rootDir,
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
    projects: [
      {
        extends: true,
        test: {
          name: 'unit',
          // 默认提供轻量级浏览器全局对象（window、localStorage 等），纯 Node 用例可按需用 @vitest-environment node 覆盖
          environment: 'happy-dom',
          include: ['src/**/*.{test,spec}.{ts,tsx}'],
          exclude: [
            ...configDefaults.exclude,
            'src/**/*.browser.{test,spec}.{ts,tsx}',
          ],
          server: {
            deps: {
              // 让依赖 bkui-vue 的蓝鲸系包统一走 Vite 管线解析别名与样式
              inline: ['bkui-vue', /^@blueking\//],
            },
          },
        },
      },
      {
        extends: true,
        optimizeDeps: {
          // 预构建浏览器组件测试高频依赖，避免执行中途触发动态 optimizeDeps 重载导致导入中断
          include: [
            '@blueking/login-modal',
            '@blueking/platform-config',
            '@blueking/xss-filter',
            'axios',
            'bkui-vue',
            'dayjs',
            'dayjs/locale/en',
            'dayjs/locale/zh-cn',
            'dayjs/plugin/customParseFormat',
            'dayjs/plugin/localeData',
            'dayjs/plugin/relativeTime',
            'dayjs/plugin/utc',
            'lodash-es',
            'lodash-es/memoize',
            'pinia',
            'vue-i18n',
          ],
        },
        test: {
          name: 'browser',
          include: ['src/**/*.browser.{test,spec}.{ts,tsx}'],
          exclude: [...configDefaults.exclude],
          browser: {
            enabled: true,
            headless: true,
            // 对齐桌面端标准视口，保障高度自适应表格等布局测试可复现
            viewport: {
              width: 1280,
              height: 920,
            },
            provider: playwright({
              launchOptions: browserExecutablePath ? { executablePath: browserExecutablePath } : undefined,
            }),
            instances: [{ browser: 'chromium' }],
          },
        },
      },
    ],
  },
});
