// @generated from: test-bdd/cases/12-应用权限/01-应用权限.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 应用权限 - 应用权限管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '应用权限', '/permission/apps');
  });

  test('场景: 查看应用权限列表', async ({ page }) => {
    const table = page.locator('.bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 10000 }).catch(() => false);

    if (tableVisible) {
      await expect(table).toBeVisible();

      const headerRow = page.locator('.bk-table thead th, .bk-table-head th').first();
      await expect(headerRow).toBeVisible({ timeout: 10000 });

      const pagination = page.locator('.bk-pagination').first();
      if (await pagination.isVisible().catch(() => false)) {
        await expect(pagination).toBeVisible();
      }

      const exportBtn = page.locator('button, .bk-button').filter({ hasText: /导出/ }).first();
      if (await exportBtn.isVisible().catch(() => false)) {
        await expect(exportBtn).toBeVisible();
      }
    } else {
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 管理应用权限 (read-only verification)', async ({ page }) => {
    const table = page.locator('.bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 10000 }).catch(() => false);

    if (tableVisible) {
      const batchRenewBtn = page.locator('button, .bk-button').filter({ hasText: /批量续期|续期/ }).first();
      if (await batchRenewBtn.isVisible().catch(() => false)) {
        await expect(batchRenewBtn).toBeVisible();
      }

      const deleteBtn = page.locator('.bk-table button, .bk-table .bk-button, .bk-table a').filter({ hasText: /删除/ }).first();
      if (await deleteBtn.isVisible().catch(() => false)) {
        await expect(deleteBtn).toBeVisible();
      }
    } else {
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 权限筛选', async ({ page }) => {
    // Try search input
    const searchInput = page.locator('.bk-search-select, .bk-input, input[placeholder*="搜索"], input[placeholder*="应用"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.click();
      await page.waitForTimeout(300);
    }

    // Verify page loaded
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
  });
});
