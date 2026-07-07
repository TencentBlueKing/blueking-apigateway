// @generated from: test-bdd/cases/25-平台工具/01-平台工具.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const { BASE_URL, reAuth, waitForPageReady } = require('../../runtime/helpers');

async function gotoPlatformTool(page, path) {
  const url = `${BASE_URL.replace(/\/$/, '')}${path}`;
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await waitForPageReady(page);
  const loginVisible = await page.locator('button').filter({ hasText: /Log in|立即登录/ }).first()
    .isVisible({ timeout: 1000 })
    .catch(() => false);
  if (page.url().includes('/login/') || loginVisible) {
    await reAuth(page);
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await waitForPageReady(page);
  }
  const pathname = path.split('?')[0];
  await expect(page).toHaveURL(new RegExp(pathname.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
}

async function useToolbox(page, toolboxId) {
  await gotoPlatformTool(page, `/platform-tools/toolbox?toolbox_id=${toolboxId}`);
  await expect(page).toHaveURL(/\/platform-tools\/toolbox/);
}

test.describe('功能: 平台工具 - 平台工具集', () => {
  test('场景: 工具箱本地转换工具', async ({ page }) => {
    await useToolbox(page, 6);
    await page.locator('textarea').first().fill('hello bdd');
    await page.locator('button').filter({ hasText: '编码' }).first().click();
    await expect(page.locator('body')).toContainText('aGVsbG8gYmRk');

    await useToolbox(page, 5);
    await page.locator('textarea').first().fill('hello bdd');
    await page.locator('button').filter({ hasText: '编码' }).first().click();
    await expect(page.locator('body')).toContainText('hello%20bdd');

    await useToolbox(page, 4);
    await page.locator('textarea').first().fill('{"name":"bdd"}');
    await page.locator('button').filter({ hasText: '格式化' }).first().click();
    await expect(page.locator('body')).toContainText('"name": "bdd"');

    await useToolbox(page, 3);
    await page.locator('textarea').first().fill('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiZGQifQ.signature');
    await page.locator('button').filter({ hasText: '解密' }).first().click();
    await expect(page.locator('body')).toContainText('bdd');
  });

  test('场景: 工具箱日志和 Trace 查询入口', async ({ page }) => {
    await useToolbox(page, 1);
    await page.locator('input[placeholder*="request_id"]').first().fill('bdd-not-exist-request-id');
    await page.locator('button').filter({ hasText: '查询' }).first().click();
    await expect(page.locator('body')).toContainText(/查询结果|暂无数据|无数据|搜索/);

    await useToolbox(page, 2);
    const traceEntry = page.locator('.tool-nav-item').filter({ hasText: /调用链/ }).first();
    if (await traceEntry.isVisible()) {
      await traceEntry.click();
      await page.locator('input[placeholder*="request_id"]').first().fill('bdd-not-exist-trace-id');
      await page.locator('button').filter({ hasText: '查询' }).first().click();
      await expect(page.locator('body')).toContainText(/查询结果|暂无数据|无数据|搜索/);
    }
  });

  test('场景: 查看平台工具子页', async ({ page }) => {
    const subPages = [
      ['/platform-tools/automated-gateway', /自动化接入网关/],
      ['/platform-tools/bk-cli', /CLI|命令行/],
      ['/platform-tools/programmable-gateway', /可编程网关/],
      ['/platform-tools/micro-gateway', /微网关/],
    ];

    for (const [path, text] of subPages) {
      await gotoPlatformTool(page, path);
      await expect(page.locator('body')).toContainText(text);
    }
  });

  test('场景: 查看 BK-CLI 文档标签页', async ({ page }) => {
    await gotoPlatformTool(page, '/platform-tools/bk-cli');

    const tabs = [
      [/功能概览/, /Agent 原生设计|覆盖面广|跨网关编排/],
      [/快速开始/, /bk-cli context init|bk-cli auth login|bk-cli api/],
      [/进阶用法/, /bk-cli context create|bk-cli apigateway|list_gateways/],
    ];

    for (const [tabName, expectedText] of tabs) {
      const tab = page.locator('.bk-tab-header-item, .bk-tab-label-item, [role=tab], button').filter({ hasText: tabName }).first();
      await expect(tab).toBeVisible({ timeout: 10000 });
      await tab.click();
      await page.waitForTimeout(500);
      await expect(page.locator('body')).toContainText(expectedText);
    }
  });

});
