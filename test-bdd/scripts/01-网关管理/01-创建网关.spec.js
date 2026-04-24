// @generated from: test-bdd/cases/01-网关管理/01-创建网关.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, fillForm, getToastMessage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 网关管理 - 创建网关', () => {
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

  test('场景: 创建普通网关', async ({ page }) => {
    // 点击新建网关按钮
    await page.locator('button').filter({ hasText: '新建网关' }).click();
    await page.waitForTimeout(800);

    // 网关类型选择普通网关（默认选中）
    // 输入网关名称
    const gatewayName = `test-gw-${Date.now().toString(36)}`;
    await page.locator('input[placeholder*="小写字母"]').fill(gatewayName);
    await page.waitForTimeout(300);

    // 输入描述（选填）
    const descInput = page.locator('textarea').first();
    if (await descInput.isVisible().catch(() => false)) {
      await descInput.fill('自动化测试创建的普通网关');
    }

    // 确保公开开关已开启（默认应为开启状态）
    // 点击确定提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(2000);

    // 验证创建成功 - 页面不再显示创建弹窗
    const dialog = page.locator('.bk-dialog, .bk-sideslider').filter({ hasText: '新建网关' });
    await expect(dialog).not.toBeVisible({ timeout: 5000 });
  });

  test('场景: 创建可编程网关', async ({ page }) => {
    // 点击新建网关按钮
    await page.locator('button').filter({ hasText: '新建网关' }).click();
    await page.waitForTimeout(800);

    // 网关类型选择可编程网关
    await page.locator('label, .bk-radio-button, .bk-radio').filter({ hasText: '可编程网关' }).click();
    await page.waitForTimeout(300);

    // 输入网关名称
    const gatewayName = `test-pgw-${Date.now().toString(36)}`;
    await page.locator('input[placeholder*="小写字母"]').fill(gatewayName);
    await page.waitForTimeout(300);

    // 选择开发语言
    const langSelect = page.locator('.bk-select').filter({ hasText: /语言|language/i }).first();
    if (await langSelect.isVisible().catch(() => false)) {
      await langSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // 输入代码仓库地址
    const repoInput = page.locator('input[placeholder*="仓库"], input[placeholder*="地址"]').first();
    if (await repoInput.isVisible().catch(() => false)) {
      await repoInput.fill('https://example.com/repo.git');
    }

    // 确保公开开关已开启
    // 点击确定提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(2000);

    // 验证创建成功
    const dialog = page.locator('.bk-dialog, .bk-sideslider').filter({ hasText: '新建网关' });
    await expect(dialog).not.toBeVisible({ timeout: 5000 });
  });

  test('场景: 创建私有网关', async ({ page }) => {
    // 点击新建网关按钮
    await page.locator('button').filter({ hasText: '新建网关' }).click();
    await page.waitForTimeout(800);

    // 输入网关名称
    const gatewayName = `test-prv-${Date.now().toString(36)}`;
    await page.locator('input[placeholder*="小写字母"]').fill(gatewayName);
    await page.waitForTimeout(300);

    // 是否公开选择不公开（关闭开关按钮）
    const publicSwitch = page.locator('.bk-switcher, .bk-switch').first();
    if (await publicSwitch.isVisible().catch(() => false)) {
      // Check if currently enabled and toggle off
      const isChecked = await publicSwitch.getAttribute('class');
      if (isChecked && isChecked.includes('is-checked')) {
        await publicSwitch.click();
        await page.waitForTimeout(300);
      }
    }

    // 点击确定提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(2000);

    // 验证创建成功
    const dialog = page.locator('.bk-dialog, .bk-sideslider').filter({ hasText: '新建网关' });
    await expect(dialog).not.toBeVisible({ timeout: 5000 });
  });

  test('场景: 名称校验', async ({ page }) => {
    // 点击新建网关按钮
    await page.locator('button').filter({ hasText: '新建网关' }).click();
    await page.waitForTimeout(800);

    // 不填写名称直接提交
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(800);

    // 验证提示"请填写名称"
    const nameError1 = page.locator('.bk-form-error, .form-error, [class*="error"]').filter({ hasText: /请填写/ }).first();
    await expect(nameError1).toBeVisible({ timeout: 10000 });

    // 输入首字符不为小写字母的名称（长度大于3）
    await page.locator('input[placeholder*="小写字母"]').fill('1234invalid');
    await page.waitForTimeout(300);
    await page.locator('button').filter({ hasText: '提交' }).click();
    await page.waitForTimeout(800);

    // 验证提示名称格式错误
    const nameError2 = page.locator('.bk-form-error, .form-error, [class*="error"]').filter({ hasText: /小写字母/ }).first();
    await expect(nameError2).toBeVisible({ timeout: 10000 });
  });
});
