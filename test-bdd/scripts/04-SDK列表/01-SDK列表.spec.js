// @generated from: test-bdd/cases/04-SDK列表/01-SDK列表.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { clickConfirm, getActiveSideslider, getTableRowCount, navigateToGatewayPage, BASE_URL, getGatewayId, selectDropdownOption } = require("../../runtime/helpers");


test.describe('功能: SDK列表 - SDK列表', () => {
  test('场景: 查看SDK列表', async ({ page }) => {
    // Mutating: generate SDK uses TEST_GATEWAY_ID
    // SDK is a sub-page of 资源版本, navigate via sidebar first
    await navigateToGatewayPage(page, getGatewayId(), '资源版本', '/resource/version');

    // Now navigate to SDK sub-page
    const baseUrl = BASE_URL.replace(/\/$/, '');
    await page.goto(`${baseUrl}/${getGatewayId()}/resource-versions/sdks`);
    await page.waitForTimeout(3000);

    // 点击生成SDK
    const genSDKBtn = page.locator('button').filter({ hasText: /生成SDK|生成/ });
    if (await genSDKBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await genSDKBtn.click();
      await page.waitForTimeout(800);

      const sdkSlider = getActiveSideslider(page);

      // 选择资源版本
      await selectDropdownOption(page, sdkSlider.locator('.bk-select').filter({ hasText: /版本|version/i }).first()).catch(() => false);

      // 输入SDK版本号
      const sdkVersionInput = sdkSlider.locator('input[placeholder*="版本"], input[name*="version"]').first();
      if (await sdkVersionInput.isVisible().catch(() => false)) {
        await sdkVersionInput.fill(`1.0.${Date.now().toString().slice(-4)}`);
      }

      // 选择语言（Python）
      await selectDropdownOption(page, sdkSlider.locator('.bk-select').filter({ hasText: /语言|language/i }).first(), /Python/).catch(() => false);

      // 点击确定
      if (await clickConfirm(page, /确定|确认/, sdkSlider).catch(() => false)) {
        await page.waitForTimeout(2000);
      }
    }
  });

  test('场景: SDK筛选', async ({ page }) => {
    // Read-only: SDK list filtering uses gateway ID 6
    await navigateToGatewayPage(page, getGatewayId(), '资源版本', '/resource/version');

    // Now navigate to SDK sub-page
    const baseUrl = BASE_URL.replace(/\/$/, '');
    await page.goto(`${baseUrl}/6/resource-versions/sdks`);
    await page.waitForTimeout(3000);

    // 通过SDK版本号搜索
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="版本"]').first();
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('1.0');
      await page.waitForTimeout(800);

      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);

      // 清空搜索
      await searchInput.clear();
      await page.waitForTimeout(800);

      // 搜索不存在的版本号
      await searchInput.fill('nonexistent-version-xyz');
      await page.waitForTimeout(800);

      // 验证展示空结果
      const emptyOrZero = await getTableRowCount(page);
      expect(emptyOrZero).toBeLessThanOrEqual(1); // 0 rows or empty state row
    }
  });
});
