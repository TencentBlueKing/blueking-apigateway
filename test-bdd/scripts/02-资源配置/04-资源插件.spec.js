// @generated from: test-bdd/cases/02-资源配置/04-资源插件.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 资源插件', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 添加插件', async ({ page }) => {
    // 点击资源插件数对应的数值（第一个资源的插件数）
    const pluginCount = page.locator('table tbody tr, .bk-table-body tr').first()
      .locator('a, .link, [class*="link"]').filter({ hasText: /^\d+$/ }).first();

    if (await pluginCount.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginCount.click();
      await page.waitForTimeout(800);

      // 点击添加插件
      const addPluginBtn = page.locator('button, .bk-button').filter({ hasText: /添加插件/ });
      await addPluginBtn.click();
      await page.waitForTimeout(800);

      // 选择插件类型（CORS插件）
      const corsOption = page.locator('.plugin-item, .bk-select-option, .bk-option, label').filter({ hasText: /CORS|跨域/ }).first();
      if (await corsOption.isVisible().catch(() => false)) {
        await corsOption.click();
        await page.waitForTimeout(300);
      }

      // 点击下一步
      const nextBtn = page.locator('button').filter({ hasText: '下一步' });
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(800);
      }

      // 填写配置信息（如 allow_origins）
      const configInput = page.locator('textarea, input[placeholder*="origin"], .code-editor, .bk-textarea').first();
      if (await configInput.isVisible().catch(() => false)) {
        await configInput.fill('*');
      }

      // 点击确定
      const confirmBtn = page.locator('button').filter({ hasText: /确定|确认/ });
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('场景: 编辑插件', async ({ page }) => {
    // 点击资源插件数对应的数值
    const pluginCount = page.locator('table tbody tr, .bk-table-body tr').first()
      .locator('a, .link, [class*="link"]').filter({ hasText: /^\d+$/ }).first();

    if (await pluginCount.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginCount.click();
      await page.waitForTimeout(800);

      // 鼠标悬浮已有插件
      const pluginItem = page.locator('.plugin-item, .plugin-card, [class*="plugin"]').first();
      if (await pluginItem.isVisible().catch(() => false)) {
        await pluginItem.hover();
        await page.waitForTimeout(300);

        // 点击编辑（铅笔图标）
        const editIcon = pluginItem.locator('.icon-edit, [class*="edit"], .bk-icon').first();
        if (await editIcon.isVisible().catch(() => false)) {
          await editIcon.click();
          await page.waitForTimeout(800);

          // 修改配置信息
          const configInput = page.locator('textarea, .code-editor, .bk-textarea').first();
          if (await configInput.isVisible().catch(() => false)) {
            await configInput.clear();
            await configInput.fill('http://example.com');
          }

          // 点击确定
          await page.locator('button').filter({ hasText: /确定|确认/ }).click();
          await page.waitForTimeout(2000);

          // 验证修改成功
          const toast = await getToastMessage(page);
          expect(toast).toMatch(/成功|修改/);
        }
      }
    }
  });

  test('场景: 删除插件', async ({ page }) => {
    // 点击资源插件数对应的数值
    const pluginCount = page.locator('table tbody tr, .bk-table-body tr').first()
      .locator('a, .link, [class*="link"]').filter({ hasText: /^\d+$/ }).first();

    if (await pluginCount.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginCount.click();
      await page.waitForTimeout(800);

      // 鼠标悬浮已有插件
      const pluginItem = page.locator('.plugin-item, .plugin-card, [class*="plugin"]').first();
      if (await pluginItem.isVisible().catch(() => false)) {
        await pluginItem.hover();
        await page.waitForTimeout(300);

        // 点击删除（垃圾桶图标）
        const deleteIcon = pluginItem.locator('.icon-delete, [class*="delete"], .bk-icon').last();
        if (await deleteIcon.isVisible().catch(() => false)) {
          await deleteIcon.click();
          await page.waitForTimeout(800);

          // 确认停用
          const confirmBtn = page.locator('.bk-dialog button, .bk-dialog-footer button').filter({ hasText: /确定|确认|停用/ });
          if (await confirmBtn.isVisible().catch(() => false)) {
            await confirmBtn.click();
            await page.waitForTimeout(2000);

            // 验证停用成功
            const toast = await getToastMessage(page);
            expect(toast).toMatch(/成功|停用/);
          }
        }
      }
    }
  });
});
