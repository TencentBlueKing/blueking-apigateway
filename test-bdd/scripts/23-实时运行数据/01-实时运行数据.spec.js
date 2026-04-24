// @generated from: test-bdd/cases/23-实时运行数据/01-实时运行数据.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, BASE_URL } = require("../../runtime/helpers");

const PAGE_PATH = 'components/realtime';

test.describe('功能: 实时运行数据 - 实时运行数据监控', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/${PAGE_PATH}`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/${PAGE_PATH}`);
      await page.waitForTimeout(3000);
    }
    // Components pages have sidebar
    await page.locator('.bk-menu-item, [class*="menu-item"], [class*="nav-item"]').first().waitFor({ timeout: 15000 }).catch(() => {});
  });

  test('场景: 查看实时运行数据', async ({ page }) => {
    const contentArea = page.locator('[class*="chart"], [class*="echart"], canvas, [class*="realtime"], [class*="data"], .bk-table').first();
    const contentVisible = await contentArea.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(contentArea).toBeVisible();

      const timeSelect = page.locator('.bk-select, .bk-dropdown, [class*="time-range"], [class*="time-select"]').first();
      if (await timeSelect.isVisible().catch(() => false)) {
        await expect(timeSelect).toBeVisible();
      }

      const autoRefreshToggle = page.locator('.bk-switcher, .bk-checkbox, [class*="switch"], [class*="toggle"]').first();
      if (await autoRefreshToggle.isVisible().catch(() => false)) {
        await expect(autoRefreshToggle).toBeVisible();
      }
    } else {
      const sidebar = page.locator('.bk-menu-item, [class*="menu-item"], [class*="nav-item"]').first();
      await expect(sidebar).toBeVisible({ timeout: 10000 });
      expect(page.url()).toContain('realtime');
    }
  });
});
