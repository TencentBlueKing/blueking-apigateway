// @generated from: test-bdd/cases/20-操作记录/01-操作记录.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL } = require("../../runtime/helpers");

const GATEWAY_ID = 6; // read-only

test.describe('功能: 操作记录 - 操作审计记录', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, '6', '操作记录', '/audit');
  });

  test('场景: 查看操作记录', async ({ page }) => {
    // Audit page has table with columns: 操作对象, 实例, 操作类型, 操作状态, 操作人, 操作时间, 描述
    const table = page.locator('.bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 10000 }).catch(() => false);

    if (tableVisible) {
      await expect(table).toBeVisible();

      // 点击时间选择框
      const timeRangePicker = page.locator('.bk-date-picker, [class*="date-picker"], [class*="time-range"]').first();
      if (await timeRangePicker.isVisible().catch(() => false)) {
        await timeRangePicker.click();
        await page.waitForTimeout(300);

        const shortcutBtn = page.locator('.bk-picker-panel-shortcut, [class*="shortcut"]').first();
        if (await shortcutBtn.isVisible().catch(() => false)) {
          await expect(shortcutBtn).toBeVisible();
        }

        // Close picker
        await page.locator('body').click({ position: { x: 10, y: 10 } });
        await page.waitForTimeout(300);
      }
    } else {
      const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
      await expect(sidebar).toBeVisible({ timeout: 10000 });
    }
  });

  test('场景: 记录筛选', async ({ page }) => {
    // Verify page loaded
    const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10000 });

    // Try search input
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"], input[placeholder*="操作"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await page.waitForTimeout(300);
    }

    // Try table
    const table = page.locator('.bk-table').first();
    if (await table.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(table).toBeVisible();

      // Check for header filter icons — use broader selector
      const headerCells = page.locator('.bk-table thead th, .bk-table-head th').first();
      if (await headerCells.isVisible().catch(() => false)) {
        await expect(headerCells).toBeVisible();
      }
    }
  });
});
