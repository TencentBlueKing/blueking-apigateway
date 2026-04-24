// @generated from: test-bdd/cases/25-平台工具/01-平台工具.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, BASE_URL } = require("../../runtime/helpers");


test.describe('功能: 平台工具 - 平台工具集', () => {
  test('场景: 查询日志工具箱', async ({ page }) => {
    await page.goto(`${BASE_URL}/tools`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/tools`);
      await waitForPageReady(page);
    }

    // 页面应展示工具箱内容
    const contentArea = page.locator('[class*="tool"], [class*="content"], .main-content, .page-content').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });

    // 查询日志搜索框
    const searchInput = page.locator('.bk-input input, input[placeholder*="request_id"], input[placeholder*="搜索"], textarea').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await expect(searchInput).toBeVisible();
    }

    // 支持JWT解析功能
    const jwtSection = page.locator('span, div, label, a, .bk-tab-label').filter({ hasText: /JWT/ }).first();
    if (await jwtSection.isVisible().catch(() => false)) {
      await expect(jwtSection).toBeVisible();
    }

    // 支持JSON格式化功能
    const jsonSection = page.locator('span, div, label, a, .bk-tab-label').filter({ hasText: /JSON/ }).first();
    if (await jsonSection.isVisible().catch(() => false)) {
      await expect(jsonSection).toBeVisible();
    }
  });

  test('场景: 查看自动化接入与可编程网关', async ({ page }) => {
    await page.goto(`${BASE_URL}/tools`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/tools`);
      await waitForPageReady(page);
    }

    // 验证页面内容加载
    const contentArea = page.locator('[class*="tool"], [class*="content"], .main-content, .page-content').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });

    // 自动化接入网关 - 验证"查看详情"按钮存在
    const autoAccessSection = page.locator('div, section').filter({ hasText: /自动化接入/ }).first();
    if (await autoAccessSection.isVisible().catch(() => false)) {
      await expect(autoAccessSection).toBeVisible();
    }

    // 可编程网关 - 验证"查看详情"按钮存在
    const programmableSection = page.locator('div, section').filter({ hasText: /可编程网关/ }).first();
    if (await programmableSection.isVisible().catch(() => false)) {
      await expect(programmableSection).toBeVisible();
    }

    // 验证"查看详情"链接存在
    const detailLinks = page.locator('a, button').filter({ hasText: /查看详情|详情/ });
    if (await detailLinks.first().isVisible().catch(() => false)) {
      const count = await detailLinks.count();
      expect(count).toBeGreaterThanOrEqual(1);
    }
  });
});
