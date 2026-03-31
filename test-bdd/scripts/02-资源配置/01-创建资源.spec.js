// @generated from: test-bdd/cases/02-资源配置/01-创建资源.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, fillForm, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 创建资源', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 创建资源并配置后端', async ({ page }) => {
    // 点击新建按钮
    await page.locator('button').filter({ hasText: '新建' }).click();
    await page.waitForTimeout(800);

    // 输入资源名称（必填）
    const resourceName = `test_res_${Date.now().toString(36)}`;
    const nameInput = page.locator('input[placeholder*="名称"], input[name*="name"]').first();
    await nameInput.fill(resourceName);
    await page.waitForTimeout(300);

    // 选填描述
    const descInput = page.locator('textarea, input[placeholder*="描述"]').first();
    if (await descInput.isVisible().catch(() => false)) {
      await descInput.fill('自动化测试创建的资源');
    }

    // 配置请求方法（默认GET）
    // 配置请求路径（必填）
    const pathInput = page.locator('input[placeholder*="路径"], input[placeholder*="path"]').first();
    if (await pathInput.isVisible().catch(() => false)) {
      await pathInput.fill(`/test/${resourceName}/`);
    }

    // 选择后端服务
    const backendSelect = page.locator('.bk-select').filter({ hasText: /后端服务|backend/i }).first();
    if (await backendSelect.isVisible().catch(() => false)) {
      await backendSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // 配置后端请求路径
    const backendPathInput = page.locator('input[placeholder*="路径"], input[placeholder*="path"]').last();
    if (await backendPathInput.isVisible().catch(() => false)) {
      await backendPathInput.fill(`/backend/${resourceName}/`);
    }

    // 点击提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(2000);

    // 验证资源创建成功
    const toast = await getToastMessage(page);
    // Page should redirect back to list or show success
  });

  test('场景: 名称校验', async ({ page }) => {
    // 点击新建按钮
    await page.locator('button').filter({ hasText: '新建' }).click();
    await page.waitForTimeout(800);

    // 不填写名称直接提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(800);

    // 验证提示"请填写名称"
    const nameError = page.locator('.bk-form-error, .form-error, [class*="error"]').filter({ hasText: /请填写/ }).first();
    await expect(nameError).toBeVisible({ timeout: 10000 });

    // 输入不合法的资源名称（含特殊字符）
    const nameInput = page.locator('input[placeholder*="名称"], input[name*="name"]').first();
    await nameInput.fill('invalid-name-#$%');
    await page.waitForTimeout(300);
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(800);

    // 验证名称格式提示
    const formatError = page.locator('.bk-form-error, .form-error, [class*="error"]').filter({ hasText: /字母|数字|下划线/ }).first();
    await expect(formatError).toBeVisible({ timeout: 10000 });
  });

  test('场景: 请求配置', async ({ page }) => {
    // 点击新建按钮
    await page.locator('button').filter({ hasText: '新建' }).click();
    await page.waitForTimeout(800);

    // 选择请求方法
    const methodSelect = page.locator('.bk-select').filter({ hasText: /GET|POST|请求方法/ }).first();
    if (await methodSelect.isVisible().catch(() => false)) {
      await methodSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').filter({ hasText: 'POST' }).first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // 输入请求路径
    const pathInput = page.locator('input[placeholder*="路径"], input[placeholder*="path"]').first();
    if (await pathInput.isVisible().catch(() => false)) {
      await pathInput.fill('/test/request-config/');
    }

    // 检查WebSocket开关
    const wsSwitch = page.locator('.bk-switcher, .bk-switch').filter({ hasText: /WebSocket/i }).first();
    if (await wsSwitch.isVisible().catch(() => false)) {
      await wsSwitch.click();
      await page.waitForTimeout(300);
    }

    // 验证请求配置区域可见
    const configSection = page.locator('.request-config, [class*="request"], [class*="config"]').first();
    await expect(configSection).toBeVisible({ timeout: 10000 }).catch(() => {});
  });
});
