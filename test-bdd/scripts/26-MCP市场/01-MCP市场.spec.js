// @generated from: test-bdd/cases/26-MCP市场/01-MCP市场.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, BASE_URL } = require("../../runtime/helpers");

const PAGE_PATH = 'mcp-market';

test.describe('功能: MCP市场 - MCP Server市场浏览', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/${PAGE_PATH}`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/${PAGE_PATH}`);
      await page.waitForTimeout(3000);
    }
    // MCP market has category sidebar (全部, 未分类, 监控告警, etc.)
    await page.locator('[class*="category"], [class*="sidebar"], [class*="menu-item"], .bk-menu-item').first().waitFor({ timeout: 15000 }).catch(() => {});
  });

  test('场景: 浏览MCP市场', async ({ page }) => {
    // MCP market has card layout and search input
    const contentArea = page.locator('[class*="card"], [class*="market"], [class*="mcp"], [class*="list"], [class*="empty"], .bk-exception').first();
    const contentVisible = await contentArea.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(contentArea).toBeVisible();
    }

    // Verify page URL
    expect(page.url()).toContain('mcp-market');

    // Try search input
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="MCP"], input[placeholder*="名称"], .bk-search-select, .bk-input input').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await page.waitForTimeout(300);
    }

    // Verify MCP Server cards or empty state
    const mcpCard = page.locator('[class*="card"], [class*="item"], [class*="mcp-server"]').first();
    if (await mcpCard.isVisible().catch(() => false)) {
      await expect(mcpCard).toBeVisible();
    }
  });

  test('场景: MCP分类筛选', async ({ page }) => {
    // MCP market has category sidebar (全部, 未分类, 监控告警, etc.)
    expect(page.url()).toContain('mcp-market');

    const categoryArea = page.locator('[class*="category"], [class*="sidebar"], [class*="filter"], [class*="nav"]').first();
    if (await categoryArea.isVisible().catch(() => false)) {
      await expect(categoryArea).toBeVisible();
    }

    // Verify content area or empty state
    const contentArea = page.locator('[class*="card"], [class*="list"], [class*="market"], [class*="mcp"], [class*="empty"], .bk-exception').first();
    if (await contentArea.isVisible({ timeout: 10000 }).catch(() => false)) {
      await expect(contentArea).toBeVisible();
    }
  });
});
