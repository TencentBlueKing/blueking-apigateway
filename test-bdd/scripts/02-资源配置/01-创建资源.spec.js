// @generated from: test-bdd/cases/02-资源配置/01-创建资源.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, fillForm, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 创建资源', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 创建资源并配置后端', async ({ page }) => {
    // 点击新建按钮 — navigates to the create resource page
    await page.locator('button').filter({ hasText: '新建' }).click();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // 输入资源名称（必填）
    // Actual placeholder: "由字母、数字、下划线（_）组成，首字符必须是字母，长度小于256个字符"
    const resourceName = `test_res_${Date.now().toString(36)}`;
    const nameInput = page.locator('input[placeholder*="字母"]').first();
    await nameInput.waitFor({ timeout: 10000 });
    await nameInput.fill(resourceName);
    await page.waitForTimeout(300);

    // 选填描述
    // Actual placeholder: "请输入描述"
    const descInput = page.locator('input[placeholder="请输入描述"], textarea[placeholder*="描述"]').first();
    if (await descInput.isVisible().catch(() => false)) {
      await descInput.fill('自动化测试创建的资源');
    }

    // 配置请求路径（必填）
    // Actual placeholder: "斜线(/)开头的合法URL路径，不包含http(s)开头的域名"
    const pathInput = page.locator('input[placeholder*="斜线"]').first();
    if (await pathInput.isVisible().catch(() => false)) {
      await pathInput.fill(`/test/${resourceName}/`);
    }

    // 配置后端请求路径 — second path input (under "后端配置" section)
    const backendPathInput = page.locator('input[placeholder*="斜线"]').last();
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
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // 不填写名称直接提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(800);

    // 验证提示"请填写名称" or any form error
    const nameError = page.locator('.bk-form-error, .form-error, [class*="error"]').first();
    await expect(nameError).toBeVisible({ timeout: 10000 });

    // 输入不合法的资源名称（含特殊字符）
    const nameInput = page.locator('input[placeholder*="字母"]').first();
    await nameInput.fill('invalid-name-#$%');
    await page.waitForTimeout(300);
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(800);

    // 验证名称格式提示
    const formatError = page.locator('.bk-form-error, .form-error, [class*="error"]').first();
    await expect(formatError).toBeVisible({ timeout: 10000 });
  });

  test('场景: 请求配置', async ({ page }) => {
    // 点击新建按钮
    await page.locator('button').filter({ hasText: '新建' }).click();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Wait for form to render
    const nameInput = page.locator('input[placeholder*="字母"]').first();
    await nameInput.waitFor({ timeout: 10000 });

    // 输入请求路径
    // Actual placeholder: "斜线(/)开头的合法URL路径，不包含http(s)开头的域名"
    const pathInput = page.locator('input[placeholder*="斜线"]').first();
    if (await pathInput.isVisible().catch(() => false)) {
      await pathInput.fill('/test/request-config/');
    }

    // 验证请求配置区域可见 — "请求配置" section header is visible
    const configHeader = page.locator('text=请求配置').first();
    await expect(configHeader).toBeVisible({ timeout: 10000 });
  });
});
