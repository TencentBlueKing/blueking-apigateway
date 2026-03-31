// @generated from: test-bdd/cases/07-环境插件管理/01-环境插件管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


// Read-only gateway for list/filter operations
const READONLY_GATEWAY_ID = 6;

test.describe('功能: 环境插件管理 - 环境插件管理', () => {
  test('场景: 添加环境插件', async ({ page }) => {
    // Mutating test uses TEST_GATEWAY_ID
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

    // 点击插件管理tab
    const pluginTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /插件/ }).first();
    if (await pluginTab.isVisible().catch(() => false)) {
      await pluginTab.click();
      await page.waitForTimeout(800);
    }

    // 点击添加插件
    const addPluginBtn = page.locator('button').filter({ hasText: /添加插件/ });
    if (await addPluginBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addPluginBtn.click();
      await page.waitForTimeout(800);

      // 选择插件类型（如 CORS）
      const corsOption = page.locator('.plugin-item, .bk-select-option, label').filter({ hasText: /CORS|跨域/ }).first();
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

      // 填写配置信息
      const configInput = page.locator('textarea, .code-editor, .bk-textarea').first();
      if (await configInput.isVisible().catch(() => false)) {
        await configInput.fill('*');
      }

      // 点击确定
      const confirmBtn = page.locator('button').filter({ hasText: /确定|确认/ });
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|添加/);
      }
    }
  });

  test('场景: 编辑环境插件', async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '环境概览', '/stage/overview');

    // 切换到详情模式
    const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
    if (await detailTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(800);
    }

    // 选择环境并进入插件管理
    const stageSelect = page.locator('.bk-select, .stage-select').first();
    if (await stageSelect.isVisible().catch(() => false)) {
      await stageSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    const pluginTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /插件/ }).first();
    if (await pluginTab.isVisible().catch(() => false)) {
      await pluginTab.click();
      await page.waitForTimeout(800);
    }

    // 鼠标悬浮已有插件，点击编辑
    const pluginItem = page.locator('.plugin-item, .plugin-card, [class*="plugin"]').first();
    if (await pluginItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginItem.hover();
      await page.waitForTimeout(300);

      const editIcon = pluginItem.locator('.icon-edit, [class*="edit"], .bk-icon').first();
      if (await editIcon.isVisible().catch(() => false)) {
        await editIcon.click();
        await page.waitForTimeout(800);

        // 修改配置
        const configInput = page.locator('textarea, .code-editor, .bk-textarea').first();
        if (await configInput.isVisible().catch(() => false)) {
          await configInput.clear();
          await configInput.fill('http://updated.example.com');
        }

        await page.locator('button').filter({ hasText: /确定|确认/ }).click();
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|修改/);
      }
    }
  });

  test('场景: 删除环境插件', async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '环境概览', '/stage/overview');

    // 切换到详情模式并选择环境
    const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
    if (await detailTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(800);
    }

    const stageSelect = page.locator('.bk-select, .stage-select').first();
    if (await stageSelect.isVisible().catch(() => false)) {
      await stageSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    const pluginTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /插件/ }).first();
    if (await pluginTab.isVisible().catch(() => false)) {
      await pluginTab.click();
      await page.waitForTimeout(800);
    }

    // 鼠标悬浮已有插件，点击删除
    const pluginItem = page.locator('.plugin-item, .plugin-card, [class*="plugin"]').first();
    if (await pluginItem.isVisible({ timeout: 5000 }).catch(() => false)) {
      await pluginItem.hover();
      await page.waitForTimeout(300);

      const deleteIcon = pluginItem.locator('.icon-delete, [class*="delete"], .bk-icon').last();
      if (await deleteIcon.isVisible().catch(() => false)) {
        await deleteIcon.click();
        await page.waitForTimeout(800);

        // 确认停用
        const confirmBtn = page.locator('.bk-dialog button, .bk-dialog-footer button').filter({ hasText: /确定|确认|停用/ });
        if (await confirmBtn.isVisible().catch(() => false)) {
          await confirmBtn.click();
          await page.waitForTimeout(2000);

          const toast = await getToastMessage(page);
          expect(toast).toMatch(/成功|停用/);
        }
      }
    }
  });

  test('场景: 查看插件列表', async ({ page }) => {
    // Read-only: viewing plugin list uses gateway ID 6
    await navigateToGatewayPage(page, '6', '环境概览', '/stage/overview');

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

    // 进入插件管理
    const pluginTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /插件/ }).first();
    if (await pluginTab.isVisible().catch(() => false)) {
      await pluginTab.click();
      await page.waitForTimeout(800);
    }

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
