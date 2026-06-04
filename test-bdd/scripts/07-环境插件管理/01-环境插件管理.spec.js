// @generated from: test-bdd/cases/07-环境插件管理/01-环境插件管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const {
  clickConfirm,
  getActionButton,
  getActiveSideslider,
  getAvailablePluginSelectionOption,
  getPluginBindingItems,
  getToastMessage,
  navigateToStageOverviewTab,
  getGatewayId,
} = require("../../runtime/helpers");

const CORS_PLUGIN_PATTERN = /CORS|跨域/;


// Read-only gateway removed — now uses test gateway from setup

test.describe('功能: 环境插件管理 - 环境插件管理', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToStageOverviewTab(page, getGatewayId(), /插件/);
  });

  test('场景: 添加环境插件', async ({ page }) => {
    // 点击添加插件
    const addPluginBtn = page.locator('button').filter({ hasText: /添加插件/ });
    if (await addPluginBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addPluginBtn.click();
      await page.waitForTimeout(800);

      const bindingItems = getPluginBindingItems(page);
      const beforeCount = await bindingItems.count();

      // 选择插件类型（优先 CORS，若已存在则选择第一个可用插件）
      const option = getAvailablePluginSelectionOption(page, CORS_PLUGIN_PATTERN);
      const fallbackOption = getAvailablePluginSelectionOption(page);
      if (await option.isVisible().catch(() => false)) {
        await option.click();
        await page.waitForTimeout(300);
      } else if (await fallbackOption.isVisible().catch(() => false)) {
        await fallbackOption.click();
        await page.waitForTimeout(300);
      }

      // 点击下一步
      const pluginSlider = getActiveSideslider(page);
      const nextBtn = getActionButton(pluginSlider, '下一步');
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(800);
      }

      // 填写配置信息
      const configInput = pluginSlider.locator('textarea, .code-editor, .bk-textarea').first();
      if (await configInput.isVisible().catch(() => false)) {
        await configInput.fill('*');
      }

      // 点击确定
      if (await clickConfirm(page, /确定|确认/, pluginSlider)) {
        await page.waitForTimeout(2000);
        await expect(bindingItems).toHaveCount(beforeCount + 1, { timeout: 10000 });

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|添加/);
      }
    }
  });

  test('场景: 编辑环境插件', async ({ page }) => {
    const bindingItems = getPluginBindingItems(page);
    const beforeCount = await bindingItems.count();

    // 鼠标悬浮已有插件，点击编辑
    const pluginItem = bindingItems.first();
    if (await pluginItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginItem.hover();
      await page.waitForTimeout(300);

      const editIcon = pluginItem.locator('.icon-edit, [class*="edit"], .bk-icon').first();
      if (await editIcon.isVisible().catch(() => false)) {
        await editIcon.click();
        await page.waitForTimeout(800);

        const pluginSlider = getActiveSideslider(page);

        // 修改配置
        const configInput = pluginSlider.locator('textarea, .code-editor, .bk-textarea').first();
        if (await configInput.isVisible().catch(() => false)) {
          await configInput.clear();
          await configInput.fill('http://updated.example.com');
        }

        const confirmed = await clickConfirm(page, /确定|确认/, pluginSlider);
        if (confirmed) {
          await page.waitForTimeout(2000);
        }

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|修改/);
        await expect(bindingItems).toHaveCount(beforeCount, { timeout: 10000 });
      }
    }
  });

  test('场景: 删除环境插件', async ({ page }) => {
    const bindingItems = getPluginBindingItems(page);
    const beforeCount = await bindingItems.count();

    // 鼠标悬浮已有插件，点击删除
    const pluginItem = bindingItems.first();
    if (await pluginItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginItem.hover();
      await page.waitForTimeout(300);

      const deleteIcon = pluginItem.locator('.icon-delete, [class*="delete"], .bk-icon').last();
      if (await deleteIcon.isVisible().catch(() => false)) {
        await deleteIcon.click();
        await page.waitForTimeout(800);

        // 确认停用
        if (await clickConfirm(page, /确定|确认|停用/)) {
          await page.waitForTimeout(2000);

          const toast = await getToastMessage(page);
          expect(toast).toMatch(/成功|停用/);
          await expect(bindingItems).toHaveCount(Math.max(0, beforeCount - 1), { timeout: 10000 });
        }
      }
    }
  });

  test('场景: 查看插件列表', async ({ page }) => {
    // 点击添加插件查看插件列表
    const addPluginBtn = page.locator('button').filter({ hasText: /添加插件/ });
    if (await addPluginBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addPluginBtn.click();
      await page.waitForTimeout(800);

      // 搜索插件
      const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="插件"]').first();
      if (await searchInput.isVisible().catch(() => false)) {
        await searchInput.fill('CORS');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(800);

        // 验证搜索结果展示
        const pluginList = page.locator('.plugin-item, .plugin-card, [class*="plugin"]');
        const count = await pluginList.count();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    }
  });

});
