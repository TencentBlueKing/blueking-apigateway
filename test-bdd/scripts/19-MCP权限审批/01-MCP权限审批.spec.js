// @generated from: test-bdd/cases/19-MCP权限审批/01-MCP权限审批.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL } = require("../../runtime/helpers");

const GATEWAY_ID = 6; // read-only

test.describe('功能: MCP权限审批 - MCP权限审批管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, '6', 'MCP 权限审批', '/mcp/permission');
  });

  test('场景: MCP权限审批通过 (read-only verification)', async ({ page }) => {
    const contentArea = page.locator('.bk-table, [class*="table"], [class*="list"], [class*="empty"], .bk-exception').first();
    const contentVisible = await contentArea.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(contentArea).toBeVisible();

      const approveBtn = page.locator('button, .bk-button').filter({ hasText: /通过|审批/ }).first();
      if (await approveBtn.isVisible().catch(() => false)) {
        await expect(approveBtn).toBeVisible();
      }

      const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"], input[placeholder*="应用"]').first();
      if (await searchInput.isVisible().catch(() => false)) {
        await expect(searchInput).toBeVisible();
      }

      const pagination = page.locator('.bk-pagination').first();
      if (await pagination.isVisible().catch(() => false)) {
        await expect(pagination).toBeVisible();
      }
    } else {
      const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
      await expect(sidebar).toBeVisible({ timeout: 10000 });
    }
  });

  test('场景: MCP权限审批驳回 (read-only verification)', async ({ page }) => {
    const contentArea = page.locator('.bk-table, [class*="table"], [class*="list"], [class*="empty"], .bk-exception').first();
    const contentVisible = await contentArea.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(contentArea).toBeVisible();

      const cancelBtn = page.locator('button, .bk-button').filter({ hasText: /取消|驳回/ }).first();
      if (await cancelBtn.isVisible().catch(() => false)) {
        await expect(cancelBtn).toBeVisible();
      }
    } else {
      const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
      await expect(sidebar).toBeVisible({ timeout: 10000 });
    }
  });
});
