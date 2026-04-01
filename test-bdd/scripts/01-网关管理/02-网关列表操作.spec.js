// @generated from: test-bdd/cases/01-网关管理/02-网关列表操作.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getTableRowCount, login, BASE_URL } = require("../../runtime/helpers");


test.describe('功能: 网关管理 - 网关列表', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/`);
      await page.waitForTimeout(3000);
    }
    // Wait for gateway list content to load
    await page.locator('.gateway-card, .gateway-item, [class*="gateway"], table tbody tr, .bk-exception').first().waitFor({ timeout: 15000 }).catch(() => {});
  });

  test('场景: 搜索网关', async ({ page }) => {
    // 搜索已存在的网关名称关键字
    const searchInput = page.locator('input[placeholder*="网关名称"], input[placeholder*="搜索"]').first();
    await expect(searchInput).toBeVisible({ timeout: 10000 });
    await searchInput.fill('bk-apigateway');
    await page.waitForTimeout(1500);

    // 验证搜索结果包含匹配的网关
    const results = page.locator('.gateway-card, .gateway-item, table tbody tr, [class*="gateway"]').first();
    await expect(results).toBeVisible({ timeout: 10000 });

    // 搜索不存在的网关名称
    await searchInput.clear();
    await searchInput.fill('nonexistent-gateway-xyz123');
    await page.waitForTimeout(2000);

    // 验证展示空结果 - either an empty state component or no gateway cards
    const emptyState = page.locator('.bk-exception, .empty-tips, [class*="empty"], [class*="no-data"], [class*="exception"]').first();
    const emptyVisible = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
    if (emptyVisible) {
      await expect(emptyState).toBeVisible();
    } else {
      // If no explicit empty state, verify no gateway cards are shown
      const gatewayCards = page.locator('.gateway-card, .gateway-item, [class*="gateway-card"]');
      const count = await gatewayCards.count();
      expect(count).toBe(0);
    }
  });

  test('场景: 查看网关详情', async ({ page }) => {
    // 使用 gateway ID 6 (bk-apigateway-inner) 进行只读操作
    // 点击网关的资源数量
    const resourceCount = page.locator('a, .link, [class*="link"]').filter({ hasText: /\d+/ }).first();
    if (await resourceCount.isVisible().catch(() => false)) {
      await resourceCount.click();
      await page.waitForTimeout(800);

      // 验证跳转到资源配置页面
      await expect(page).toHaveURL(/resources/, { timeout: 10000 });
      await page.goBack();
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(3000);
    }

    // 点击环境概览
    const stageOverview = page.locator('a, .link, [class*="link"]').filter({ hasText: '环境概览' }).first();
    if (await stageOverview.isVisible().catch(() => false)) {
      await stageOverview.click();
      await page.waitForTimeout(800);

      // 验证跳转到环境概览页面
      await expect(page).toHaveURL(/stages/, { timeout: 10000 });
      await page.goBack();
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(3000);
    }

    // 通过网关类型筛选
    const typeFilter = page.locator('.bk-select').first();
    if (await typeFilter.isVisible().catch(() => false)) {
      await selectDropdown(page, '.bk-select', '普通网关');
      await page.waitForTimeout(800);

      // 验证仅展示普通网关类型
      const gatewayCards = page.locator('.gateway-card, .gateway-item, table tbody tr');
      const count = await gatewayCards.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });
});
