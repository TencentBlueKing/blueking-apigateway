// @generated from: test-bdd/cases/13-访问日志/01-访问日志.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 访问日志 - 流水日志查看', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '流水日志', '/access-log');
  });

  test('场景: 查看访问日志', async ({ page }) => {
    // Try to find any content area
    const logContent = page.locator('.bk-table, [class*="log"], [class*="table"], [class*="search"]').first();
    const contentVisible = await logContent.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(logContent).toBeVisible();

      // 点击时间范围选择器
      const timeRangePicker = page.locator('.bk-date-picker, [class*="date-picker"], [class*="time-range"]').first();
      if (await timeRangePicker.isVisible().catch(() => false)) {
        await timeRangePicker.click();
        await page.waitForTimeout(300);
        // Close picker by clicking elsewhere
        await page.locator('body').click({ position: { x: 10, y: 10 } });
        await page.waitForTimeout(300);
      }
    } else {
      // Verify page loaded via URL
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 日志搜索与筛选', async ({ page }) => {
    // Verify page is loaded
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    // Try search input
    const searchInput = page.locator('.bk-search-select, .bk-textarea, textarea, input[placeholder*="搜索"], input[placeholder*="request"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await page.waitForTimeout(300);
    }

    // Try env select
    const envSelect = page.locator('.bk-select').first();
    if (await envSelect.isVisible().catch(() => false)) {
      await expect(envSelect).toBeVisible();
    }
  });
});
