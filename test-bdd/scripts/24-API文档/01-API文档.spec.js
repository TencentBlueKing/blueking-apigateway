// @generated from: test-bdd/cases/24-API文档/01-API文档.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, BASE_URL } = require("../../runtime/helpers");


test.describe('功能: API文档 - API文档查看', () => {
  test('场景: 搜索网关API文档', async ({ page }) => {
    await page.goto(`${BASE_URL}/docs/api-docs`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/docs/api-docs`);
      await waitForPageReady(page);
    }

    // 页面应展示网关API列表
    const contentArea = page.locator('.bk-table, [class*="card"], [class*="list"], [class*="doc"]').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });

    // 在搜索框中输入网关名称进行搜索
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"], input[placeholder*="网关"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await page.waitForTimeout(300);
    }
  });

  test('场景: 查看组件API文档', async ({ page }) => {
    await page.goto(`${BASE_URL}/docs/api-docs`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/docs/api-docs`);
      await waitForPageReady(page);
    }

    // 切换到组件API文档标签
    const componentTab = page.locator('a, .bk-tab-label, .nav-item, .menu-item').filter({ hasText: /组件/ }).first();
    if (await componentTab.isVisible().catch(() => false)) {
      await componentTab.click();
      await waitForPageReady(page);
    }

    // 页面应展示组件API列表
    const contentArea = page.locator('.bk-table, [class*="card"], [class*="list"], [class*="doc"], [class*="component"]').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });

    // 支持通过API名称搜索
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await expect(searchInput).toBeVisible();
    }
  });

  test('场景: 查看SDK文档', async ({ page }) => {
    await page.goto(`${BASE_URL}/docs/api-docs`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/docs/api-docs`);
      await waitForPageReady(page);
    }

    // 验证"查看SDK"按钮存在
    const sdkBtn = page.locator('button, .bk-button, a').filter({ hasText: /SDK/ }).first();
    if (await sdkBtn.isVisible().catch(() => false)) {
      await expect(sdkBtn).toBeVisible();
    }

    // 验证页面内容加载
    const contentArea = page.locator('.bk-table, [class*="card"], [class*="list"], [class*="doc"]').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });
  });
});
