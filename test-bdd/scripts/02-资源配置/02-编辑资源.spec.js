// @generated from: test-bdd/cases/02-资源配置/02-编辑资源.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 编辑资源', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 编辑基础信息', async ({ page }) => {
    // 点击资源列表中的第一个编辑按钮
    const editBtn = page.locator('button, a, .bk-button').filter({ hasText: '编辑' }).first();
    await expect(editBtn).toBeVisible({ timeout: 10000 });
    await editBtn.click();
    await page.waitForTimeout(800);

    // 修改描述信息
    const descInput = page.locator('textarea, input[placeholder*="描述"]').first();
    if (await descInput.isVisible().catch(() => false)) {
      await descInput.clear();
      await descInput.fill(`自动化测试编辑 - ${Date.now()}`);
    }

    // 点击提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(2000);

    // 验证更新成功
    const toast = await getToastMessage(page);
    expect(toast).toMatch(/成功|更新/);
  });

  test('场景: 编辑后端配置', async ({ page }) => {
    // 点击资源列表中的第一个编辑按钮
    const editBtn = page.locator('button, a, .bk-button').filter({ hasText: '编辑' }).first();
    await expect(editBtn).toBeVisible({ timeout: 10000 });
    await editBtn.click();
    await page.waitForTimeout(800);

    // 修改后端请求路径
    const backendPathInput = page.locator('input[placeholder*="路径"], input[placeholder*="path"]').last();
    if (await backendPathInput.isVisible().catch(() => false)) {
      await backendPathInput.clear();
      await backendPathInput.fill(`/backend/updated-${Date.now()}/`);
    }

    // 点击提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(2000);

    // 验证更新成功
    const toast = await getToastMessage(page);
    expect(toast).toMatch(/成功|更新/);
  });
});
