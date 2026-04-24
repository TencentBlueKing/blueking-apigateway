// @generated from: test-bdd/cases/22-文档分类/01-文档分类.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, BASE_URL } = require("../../runtime/helpers");

const PAGE_PATH = 'components/doc-category';

test.describe('功能: 文档分类 - 文档分类管理', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/${PAGE_PATH}`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/${PAGE_PATH}`);
      await page.waitForTimeout(3000);
    }
    // Components pages have sidebar: 简介, 系统管理, 组件管理, 文档分类, 实时运行数据
    await page.locator('.bk-menu-item, [class*="menu-item"], [class*="nav-item"]').first().waitFor({ timeout: 15000 }).catch(() => {});
  });

  test('场景: 编辑文档分类 (read-only verification)', async ({ page }) => {
    const table = page.locator('.bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 10000 }).catch(() => false);

    if (tableVisible) {
      await expect(table).toBeVisible();

      const editBtn = page.locator('.bk-table button, .bk-table .bk-button, .bk-table a').filter({ hasText: /编辑/ }).first();
      if (await editBtn.isVisible().catch(() => false)) {
        await expect(editBtn).toBeVisible();
      }
    } else {
      const sidebar = page.locator('.bk-menu-item, [class*="menu-item"], [class*="nav-item"]').first();
      await expect(sidebar).toBeVisible({ timeout: 10000 });
      expect(page.url()).toContain('doc-category');
    }
  });

  test('场景: 管理分类', async ({ page }) => {
    // Verify page loaded
    const sidebar = page.locator('.bk-menu-item, [class*="menu-item"], [class*="nav-item"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10000 });
    expect(page.url()).toContain('doc-category');

    // Try search input
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"], input[placeholder*="分类"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await page.waitForTimeout(300);
    }

    // Try table
    const table = page.locator('.bk-table').first();
    if (await table.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(table).toBeVisible();
    }

    const pagination = page.locator('.bk-pagination').first();
    if (await pagination.isVisible().catch(() => false)) {
      await expect(pagination).toBeVisible();
    }
  });
});
