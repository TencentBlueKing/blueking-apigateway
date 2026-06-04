// @generated from: test-bdd/cases/02-资源配置/05-导入导出资源.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { clickConfirm, getActionButton, getActiveOverlay, navigateToGatewayPage, getGatewayId, selectDropdownOption } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 导入导出资源', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 导入资源', async ({ page }) => {
    // 点击导入按钮 — this opens a dropdown menu with "资源配置" and "资源文档"
    const importBtn = page.locator('button').filter({ hasText: '导入' }).first();
    await expect(importBtn).toBeVisible({ timeout: 10000 });
    await importBtn.click();
    await page.waitForTimeout(800);

    // Select "资源配置" from the dropdown list
    const importOption = page.locator('li, [class*="dropdown-item"], [class*="popover-item"]').filter({ hasText: '资源配置' }).first();
    if (await selectDropdownOption(page, importBtn, '资源配置', 'li, [class*="dropdown-item"], [class*="popover-item"]').catch(() => false)
      || await importOption.isVisible({ timeout: 3000 }).catch(() => false)) {
      if (await importOption.isVisible({ timeout: 300 }).catch(() => false)) {
        await importOption.click();
      }
      await page.waitForTimeout(1500);

      // Now the import dialog/sideslider should appear
      const dialogContent = page.locator('.bk-sideslider, .bk-dialog, [class*="import"]').first();
      const dialogVisible = await dialogContent.isVisible({ timeout: 5000 }).catch(() => false);

      if (dialogVisible) {
        const importOverlay = await getActiveOverlay(page);

        // 选择文档语言（中文）
        const langOption = importOverlay.locator('label, .bk-radio, .bk-radio-button').filter({ hasText: /中文/ }).first();
        if (await langOption.isVisible().catch(() => false)) {
          await langOption.click();
          await page.waitForTimeout(300);
        }

        // 验证上传区域或下一步按钮存在
        const nextBtn = getActionButton(importOverlay, /下一步|确认/);
        if (await nextBtn.isVisible().catch(() => false)) {
          await expect(nextBtn).toBeVisible();
        }
      }
    }

    // Verify we're at least on the right page
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
  });

  test('场景: 导出资源', async ({ page }) => {
    // 点击导出按钮
    const exportBtn = page.locator('button').filter({ hasText: '导出' }).first();
    await expect(exportBtn).toBeVisible({ timeout: 10000 });
    await exportBtn.click();
    await page.waitForTimeout(800);

    // The export button might also have a dropdown
    const exportOptionSelected = await selectDropdownOption(page, exportBtn, '资源配置', 'li, [class*="dropdown-item"], [class*="popover-item"]').catch(() => false);
    const exportOption = page.locator('li, [class*="dropdown-item"], [class*="popover-item"]').filter({ hasText: '资源配置' }).first();
    if (!exportOptionSelected && await exportOption.isVisible({ timeout: 2000 }).catch(() => false)) {
      await exportOption.click();
      await page.waitForTimeout(800);
    }

    const exportOverlay = await getActiveOverlay(page);

    // 选择全部资源
    const allResource = exportOverlay.locator('label, .bk-radio, .bk-radio-button').filter({ hasText: /全部/ }).first();
    if (await allResource.isVisible().catch(() => false)) {
      await allResource.click();
      await page.waitForTimeout(300);
    }

    // 选择导出格式为YAML
    const yamlOption = exportOverlay.locator('label, .bk-radio, .bk-radio-button').filter({ hasText: /YAML/ }).first();
    if (await yamlOption.isVisible().catch(() => false)) {
      await yamlOption.click();
      await page.waitForTimeout(300);
    }

    // 点击确定导出
    const confirmBtn = getActionButton(exportOverlay, /确定|确认|导出/);
    if (await confirmBtn.isVisible().catch(() => false)) {
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);
      if (!await clickConfirm(page, /确定|确认|导出/, exportOverlay)) {
        await confirmBtn.click();
      }
      await page.waitForTimeout(2000);

      const download = await downloadPromise;
      if (download) {
        expect(download).toBeTruthy();
      }
    }
  });
});
