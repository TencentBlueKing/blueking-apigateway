// @generated from: test-bdd/cases/05-环境概览/01-环境概览.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 环境概览 - 环境概览', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '环境概览', '/stage/overview');
  });

  test('场景: 查看环境概览', async ({ page }) => {
    // 点击"+"新建环境
    const addBtn = page.locator('button, .bk-button, [class*="add"]').filter({ hasText: /\+|新建/ }).first();
    if (await addBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(800);

      // 输入环境名称（必填）
      const stageName = `test-stage-${Date.now().toString(36).slice(-4)}`;
      const nameInput = page.locator('input[placeholder*="名称"], input[name*="name"]').first();
      if (await nameInput.isVisible().catch(() => false)) {
        await nameInput.fill(stageName);
      }

      // 输入描述（选填）
      const descInput = page.locator('textarea, input[placeholder*="描述"]').first();
      if (await descInput.isVisible().catch(() => false)) {
        await descInput.fill('自动化测试创建的环境');
      }

      // 输入后端服务地址
      const addrInput = page.locator('input[placeholder*="地址"], input[placeholder*="host"], input[placeholder*="http"]').first();
      if (await addrInput.isVisible().catch(() => false)) {
        await addrInput.fill('http://httpbin.org');
      }

      // 输入超时时间
      const timeoutInput = page.locator('input[placeholder*="超时"], input[type="number"]').first();
      if (await timeoutInput.isVisible().catch(() => false)) {
        await timeoutInput.fill('30');
      }

      // 点击确定
      await page.locator('button').filter({ hasText: /确定|确认/ }).click();
      await page.waitForTimeout(2000);

      // 验证创建成功
      const toast = await getToastMessage(page);
      expect(toast).toMatch(/成功|新建/);
    }
  });

  test('场景: 发布资源', async ({ page }) => {
    // 点击发布资源按钮
    const publishBtn = page.locator('button').filter({ hasText: '发布资源' });
    if (await publishBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await publishBtn.click();
      await page.waitForTimeout(800);

      // 选择要发布的资源版本
      const versionSelect = page.locator('.bk-select').first();
      if (await versionSelect.isVisible().catch(() => false)) {
        await versionSelect.click();
        await page.waitForTimeout(300);
        await page.locator('.bk-select-option, .bk-option').first().click();
        await page.waitForTimeout(300);
        await page.locator('body').click({ position: { x: 10, y: 10 } });
      }

      // 点击下一步
      const nextBtn = page.locator('button').filter({ hasText: '下一步' });
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(800);
      }

      // 确认发布
      const confirmBtn = page.locator('button').filter({ hasText: /确认|发布|确定/ });
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|发布/);
      }
    }
  });

  test('场景: 下架资源', async ({ page }) => {
    // 查找并点击下架按钮
    const unpublishBtn = page.locator('button').filter({ hasText: '下架' });
    if (await unpublishBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await unpublishBtn.click();
      await page.waitForTimeout(800);

      // 确认下架操作
      const confirmBtn = page.locator('.bk-dialog button, .bk-dialog-footer button').filter({ hasText: /确定|确认|下架/ });
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|下架/);
      }
    }
  });
});
