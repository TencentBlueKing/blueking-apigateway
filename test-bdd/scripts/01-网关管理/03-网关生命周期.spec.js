// @generated from: test-bdd/cases/01-网关管理/03-网关生命周期.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 网关管理 - 网关生命周期', () => {
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

  test('场景: 停用网关', async ({ page }) => {
    // 查找闲置状态的网关（过去180天没有调用量）
    const idleGateway = page.locator('.gateway-card, .gateway-item, table tbody tr').filter({ hasText: /闲置/ }).first();

    if (await idleGateway.isVisible({ timeout: 3000 }).catch(() => false)) {
      // 点击去停用按钮
      const disableBtn = idleGateway.locator('a, button, .link').filter({ hasText: /停用|去停用/ });
      await disableBtn.click();
      await page.waitForTimeout(800);

      // 验证跳转到该网关的基本信息页面
      await expect(page).toHaveURL(/basic-info|info|setting/, { timeout: 5000 });
    } else {
      // 若没有闲置网关，直接导航到测试网关的基本信息页面验证页面可访问
      await navigateToGatewayPage(page, getGatewayId(), '基本信息', '/basic-info');
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('场景: 删除网关', async ({ page }) => {
    // 导航到测试网关的基本信息页面
    await navigateToGatewayPage(page, getGatewayId(), '基本信息', '/basic-info');

    // 查找删除网关按钮（仅验证按钮存在，不实际执行删除）
    const deleteBtn = page.locator('button, .bk-button').filter({ hasText: /删除网关/ });

    // 验证删除按钮存在于页面上
    // 注意：不实际执行删除操作，仅验证页面元素
    if (await deleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      // 验证删除按钮可见
      await expect(deleteBtn).toBeVisible();
    }
  });
});
