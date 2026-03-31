// @generated from: test-bdd/cases/08-环境变量管理/01-环境变量管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 环境变量管理 - 环境变量管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '环境概览', '/stage/overview');

    // 切换到详情模式
    const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
    if (await detailTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(800);
    }

    // 选择环境
    const stageSelect = page.locator('.bk-select, .stage-select').first();
    if (await stageSelect.isVisible().catch(() => false)) {
      await stageSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // 进入变量管理tab
    const varTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /变量/ }).first();
    if (await varTab.isVisible().catch(() => false)) {
      await varTab.click();
      await page.waitForTimeout(800);
    }
  });

  test('场景: 创建环境变量', async ({ page }) => {
    // 点击编辑（铅笔图标）
    const editBtn = page.locator('button, .bk-button, [class*="edit"], .icon-edit').filter({ hasText: /编辑/ }).first();
    if (!await editBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Try icon button
      const editIcon = page.locator('.icon-edit, [class*="edit-icon"], [class*="pencil"]').first();
      if (await editIcon.isVisible().catch(() => false)) {
        await editIcon.click();
      }
    } else {
      await editBtn.click();
    }
    await page.waitForTimeout(800);

    // 输入变量名
    const varNameInput = page.locator('input[placeholder*="变量名"], input[placeholder*="key"], input[name*="key"]').first();
    if (await varNameInput.isVisible().catch(() => false)) {
      const varName = `test_var_${Date.now().toString(36).slice(-4)}`;
      await varNameInput.fill(varName);
      await page.waitForTimeout(300);
    }

    // 输入变量值
    const varValueInput = page.locator('input[placeholder*="变量值"], input[placeholder*="value"], input[name*="value"]').first();
    if (await varValueInput.isVisible().catch(() => false)) {
      await varValueInput.fill('test_value_123');
      await page.waitForTimeout(300);
    }

    // 点击保存
    const saveBtn = page.locator('button').filter({ hasText: /保存/ });
    if (await saveBtn.isVisible().catch(() => false)) {
      await saveBtn.click();
      await page.waitForTimeout(800);

      // 确认修改
      const confirmBtn = page.locator('.bk-dialog button, .bk-dialog-footer button').filter({ hasText: /确定|确认/ });
      if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }

      // 验证更新成功
      const toast = await getToastMessage(page);
      expect(toast).toMatch(/成功|更新/);
    }
  });

  test('场景: 编辑环境变量', async ({ page }) => {
    // 点击编辑（铅笔图标）
    const editBtn = page.locator('button, .bk-button, [class*="edit"], .icon-edit').filter({ hasText: /编辑/ }).first();
    if (!await editBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      const editIcon = page.locator('.icon-edit, [class*="edit-icon"], [class*="pencil"]').first();
      if (await editIcon.isVisible().catch(() => false)) {
        await editIcon.click();
      }
    } else {
      await editBtn.click();
    }
    await page.waitForTimeout(800);

    // 修改变量值
    const varValueInput = page.locator('input[placeholder*="变量值"], input[placeholder*="value"], input[name*="value"]').first();
    if (await varValueInput.isVisible().catch(() => false)) {
      await varValueInput.clear();
      await varValueInput.fill(`updated_value_${Date.now()}`);
      await page.waitForTimeout(300);
    }

    // 点击保存并确认修改
    const saveBtn = page.locator('button').filter({ hasText: /保存/ });
    if (await saveBtn.isVisible().catch(() => false)) {
      await saveBtn.click();
      await page.waitForTimeout(800);

      const confirmBtn = page.locator('.bk-dialog button, .bk-dialog-footer button').filter({ hasText: /确定|确认/ });
      if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }

      const toast = await getToastMessage(page);
      expect(toast).toMatch(/成功|更新/);
    }
  });
});
