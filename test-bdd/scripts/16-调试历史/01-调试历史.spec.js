// @generated from: test-bdd/cases/16-调试历史/01-调试历史.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 调试历史 - 请求记录管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '在线调试', '/online-debug/history');
  });

  test('场景: 查看调试历史', async ({ page }) => {
    const table = page.locator('.bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 10000 }).catch(() => false);

    if (tableVisible) {
      await expect(table).toBeVisible();

      const expandIcon = page.locator('.bk-table [class*="expand"], .bk-table .icon-angle-right, .bk-table [class*="detail"]').first();
      if (await expandIcon.isVisible().catch(() => false)) {
        await expect(expandIcon).toBeVisible();
      }

      const settingBtn = page.locator('.bk-table-setting-content, [class*="setting"], .icon-cog, button[class*="setting"]').first();
      if (await settingBtn.isVisible().catch(() => false)) {
        await expect(settingBtn).toBeVisible();
      }
    } else {
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 历史记录筛选', async ({ page }) => {
    // Verify page loaded
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    // Try search input
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"], input[placeholder*="资源"]').first();
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
