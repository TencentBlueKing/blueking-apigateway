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

import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { build, preview } from 'vite';
import vue from '@vitejs/plugin-vue';
import jsx from '@vitejs/plugin-vue-jsx';
import AutoImport from 'unplugin-auto-import/vite';

const root = import.meta.dirname;
const src = path.resolve(root, '../../src');
const temp = await mkdtemp(path.join(os.tmpdir(), 'ag-table-test-'));
const outDir = path.join(temp, 'dist');
const result = Promise.withResolvers();
let server;
let browser;
let debuggerUrl;
try {
  await build({
    root,
    configFile: false,
    publicDir: false,
    logLevel: 'error',
    css: { preprocessorMaxWorkers: 0 },
    resolve: { alias: [{
      find: '@',
      replacement: src,
    }] },
    plugins: [vue(),
      jsx(),
      AutoImport({
        imports: ['vue'],
        dts: false,
      })],
    build: {
      outDir,
      minify: false,
    },
  });
  server = await preview({
    root,
    configFile: false,
    logLevel: 'error',
    build: { outDir },
    preview: {
      host: '127.0.0.1',
      port: 0,
      open: false,
    },
    plugins: [{
      name: 'ag-table-test-result',
      configurePreviewServer(vite) {
        vite.middlewares.use('/result', async (req, res) => {
          const chunks = [];
          for await (const chunk of req) chunks.push(chunk);
          res.end();
          try {
            result.resolve(JSON.parse(Buffer.concat(chunks).toString()));
          }
          catch (error) {
            result.reject(error);
          }
        });
      },
    }],
  });
  const executable = process.env.CHROME_BIN ?? ({
    win32: path.join(process.env.ProgramFiles || 'C:/Program Files', 'Google/Chrome/Application/chrome.exe'),
    darwin: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  }[process.platform] || 'chromium');
  const url = `http://127.0.0.1:${server.httpServer.address().port}`;
  browser = spawn(executable, [
    '--headless',
    '--disable-background-networking',
    '--disable-extensions',
    '--no-first-run',
    '--disable-sync',
    '--remote-debugging-port=0',
    '--window-size=1280,920',
    `--user-data-dir=${path.join(temp, 'profile')}`,
    url,
  ], {
    windowsHide: true,
    stdio: ['ignore', 'ignore', 'pipe'],
  });
  let stderrTail = '';
  const appendStderr = (chunk) => {
    stderrTail = (stderrTail + chunk).slice(-4000);
  };
  const formatBrowserError = (message) => {
    const detail = stderrTail.trim();
    return Error(detail ? `${message}\n${detail}` : message);
  };
  browser.stderr.setEncoding('utf8').on('data', (line) => {
    appendStderr(line);
    debuggerUrl ??= line.match(/DevTools listening on (ws:\/\/\S+)/)?.[1];
  });
  browser.once('error', result.reject);
  browser.once('exit', (code, signal) => result.reject(formatBrowserError(`Browser exited with ${code ?? signal}`)));
  const timeout = setTimeout(() => result.reject(formatBrowserError('Browser test timed out')), 60000);
  try {
    const report = await result.promise;
    if (report.error) throw Error(report.error);
    console.log(`Passed ${report.checks.length} browser assertions`, report.metrics);
  }
  finally {
    clearTimeout(timeout);
  }
}
finally {
  if (browser?.pid && browser.exitCode === null && browser.signalCode === null) {
    const exited = once(browser, 'exit');
    if (debuggerUrl) {
      const socket = new WebSocket(debuggerUrl);
      socket.onopen = () => socket.send(JSON.stringify({
        id: 1,
        method: 'Browser.close',
      }));
      socket.onerror = () => browser.kill();
    }
    else {
      browser.kill();
    }
    const terminate = setTimeout(() => browser.kill(), 1500);
    await exited;
    clearTimeout(terminate);
  }
  await server?.close();
  await rm(temp, {
    recursive: true,
    force: true,
    maxRetries: 5,
    retryDelay: 150,
  });
}
