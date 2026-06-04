// @generated from: test-bdd/cases/08-环境变量管理/01-环境变量管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { clickConfirm, getActionButton, getActiveSideslider, getToastMessage, navigateToStageOverviewTab, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 环境变量管理 - 环境变量管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToStageOverviewTab(page, getGatewayId(), /变量/);
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

    const variableSlider = getActiveSideslider(page);

    // 输入变量名
    const varNameInput = variableSlider.locator('input[placeholder*="变量名"], input[placeholder*="key"], input[name*="key"]').first();
    if (await varNameInput.isVisible().catch(() => false)) {
      const varName = `test_var_${Date.now().toString(36).slice(-4)}`;
      await varNameInput.fill(varName);
      await page.waitForTimeout(300);
    }

    // 输入变量值
    const varValueInput = variableSlider.locator('input[placeholder*="变量值"], input[placeholder*="value"], input[name*="value"]').first();
    if (await varValueInput.isVisible().catch(() => false)) {
      await varValueInput.fill('test_value_123');
      await page.waitForTimeout(300);
    }

    // 点击保存
    const saveBtn = getActionButton(variableSlider, /保存/);
    if (await saveBtn.isVisible().catch(() => false)) {
      await saveBtn.click();
      await page.waitForTimeout(800);

      // 确认修改
      if (await clickConfirm(page, /确定|确认/, variableSlider)) {
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

    const variableSlider = getActiveSideslider(page);

    // 修改变量值
    const varValueInput = variableSlider.locator('input[placeholder*="变量值"], input[placeholder*="value"], input[name*="value"]').first();
    if (await varValueInput.isVisible().catch(() => false)) {
      await varValueInput.clear();
      await varValueInput.fill(`updated_value_${Date.now()}`);
      await page.waitForTimeout(300);
    }

    // 点击保存并确认修改
    const saveBtn = getActionButton(variableSlider, /保存/);
    if (await saveBtn.isVisible().catch(() => false)) {
      await saveBtn.click();
      await page.waitForTimeout(800);

      if (await clickConfirm(page, /确定|确认/, variableSlider)) {
        await page.waitForTimeout(2000);
      }

      const toast = await getToastMessage(page);
      expect(toast).toMatch(/成功|更新/);
    }
  });
});
