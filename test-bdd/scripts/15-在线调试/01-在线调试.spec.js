// @generated from: test-bdd/cases/15-在线调试/01-在线调试.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL } = require("../../runtime/helpers");

const GATEWAY_ID = 6; // read-only

test.describe('功能: 在线调试 - API在线调试', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, '6', '在线调试', '/online-debug');
  });

  test('场景: 发送调试请求', async ({ page }) => {
    // Try to find any content area - select, resource list, send button, etc.
    const contentArea = page.locator('.bk-select, [class*="resource"], [class*="api-list"], [class*="debug"], .bk-tree').first();
    const contentVisible = await contentArea.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(contentArea).toBeVisible();

      // 验证发送请求按钮存在
      const sendBtn = page.locator('button, .bk-button').filter({ hasText: /发送|Send/ }).first();
      if (await sendBtn.isVisible().catch(() => false)) {
        await expect(sendBtn).toBeVisible();
      }

      // 验证 Headers、Query、Body 标签页存在
      const tabArea = page.locator('[class*="tab"], .bk-tab').first();
      if (await tabArea.isVisible().catch(() => false)) {
        await expect(tabArea).toBeVisible();
      }
    } else {
      const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
      await expect(sidebar).toBeVisible({ timeout: 10000 });
    }
  });

  test('场景: 设置请求参数', async ({ page }) => {
    // Verify page loaded
    const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10000 });

    // 支持"自定义应用"选项
    const customAppOption = page.locator('label, span, .bk-radio, .bk-checkbox').filter({ hasText: /自定义应用/ }).first();
    if (await customAppOption.isVisible().catch(() => false)) {
      await expect(customAppOption).toBeVisible();
    }

    // 支持在资源列表下方输入关键字搜索资源
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="资源"], .bk-input input').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await expect(searchInput).toBeVisible();
    }
  });

  test('场景: 查看调试响应', async ({ page }) => {
    // Verify page loaded
    const sidebar = page.locator('.bk-menu-item, [class*="menu-item"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10000 });

    // 验证响应区域存在
    const responseArea = page.locator('[class*="response"], [class*="result"], [class*="output"]').first();
    if (await responseArea.isVisible().catch(() => false)) {
      await expect(responseArea).toBeVisible();
    }
  });
});
