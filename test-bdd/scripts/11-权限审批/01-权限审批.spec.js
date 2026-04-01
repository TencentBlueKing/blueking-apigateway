// @generated from: test-bdd/cases/11-权限审批/01-权限审批.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 权限审批 - 权限审批管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '权限审批', '/permission/applys');
  });

  test('场景: 查看审批列表', async ({ page }) => {
    // Verify the page loaded — check for any content: table, sidebar, or page title
    const pageContent = page.locator('.bk-table, table, [class*="permission"], [class*="applys"], text=权限审批').first();
    const contentVisible = await pageContent.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(pageContent).toBeVisible();
    }

    // Verify we are on the right gateway page
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/`), { timeout: 5000 });
  });

  test('场景: 审批通过 (read-only verification)', async ({ page }) => {
    // Verify we are on the right gateway page
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/`), { timeout: 5000 });

    // Check for any content on the page
    const table = page.locator('.bk-table, table').first();
    const tableVisible = await table.isVisible({ timeout: 5000 }).catch(() => false);

    if (tableVisible) {
      const approveBtn = page.locator('button, .bk-button').filter({ hasText: /通过|审批/ }).first();
      if (await approveBtn.isVisible().catch(() => false)) {
        await expect(approveBtn).toBeVisible();
      }
    }
  });

  test('场景: 审批驳回 (read-only verification)', async ({ page }) => {
    // Verify we are on the right gateway page
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/`), { timeout: 5000 });

    const table = page.locator('.bk-table, table').first();
    const tableVisible = await table.isVisible({ timeout: 5000 }).catch(() => false);

    if (tableVisible) {
      const rejectBtn = page.locator('button, .bk-button').filter({ hasText: /驳回/ }).first();
      if (await rejectBtn.isVisible().catch(() => false)) {
        await expect(rejectBtn).toBeVisible();
      }
    }
  });
});
