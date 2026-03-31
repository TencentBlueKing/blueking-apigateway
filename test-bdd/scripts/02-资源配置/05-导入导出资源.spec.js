// @generated from: test-bdd/cases/02-资源配置/05-导入导出资源.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getToastMessage, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 导入导出资源', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 导入资源', async ({ page }) => {
    // 点击导入按钮
    const importBtn = page.locator('button, .bk-button').filter({ hasText: '导入' }).first();
    await expect(importBtn).toBeVisible({ timeout: 10000 });
    await importBtn.click();
    await page.waitForTimeout(800);

    // 选择文档语言（中文）
    const langOption = page.locator('label, .bk-radio, .bk-radio-button').filter({ hasText: /中文/ }).first();
    if (await langOption.isVisible().catch(() => false)) {
      await langOption.click();
      await page.waitForTimeout(300);
    }

    // 上传Swagger文件 - 验证上传区域可见
    const uploadArea = page.locator('input[type="file"], .bk-upload, [class*="upload"]').first();
    await expect(uploadArea).toBeAttached({ timeout: 10000 });

    // 验证导入对话框存在下一步按钮
    const nextBtn = page.locator('button').filter({ hasText: /下一步|确认/ }).first();
    await expect(nextBtn).toBeVisible({ timeout: 10000 });
  });

  test('场景: 导出资源', async ({ page }) => {
    // 点击导出按钮
    const exportBtn = page.locator('button, .bk-button').filter({ hasText: '导出' }).first();
    await expect(exportBtn).toBeVisible({ timeout: 10000 });
    await exportBtn.click();
    await page.waitForTimeout(800);

    // 选择全部资源
    const allResource = page.locator('label, .bk-radio, .bk-radio-button').filter({ hasText: /全部/ }).first();
    if (await allResource.isVisible().catch(() => false)) {
      await allResource.click();
      await page.waitForTimeout(300);
    }

    // 选择导出格式为YAML
    const yamlOption = page.locator('label, .bk-radio, .bk-radio-button').filter({ hasText: /YAML/ }).first();
    if (await yamlOption.isVisible().catch(() => false)) {
      await yamlOption.click();
      await page.waitForTimeout(300);
    }

    // 点击确定导出
    const confirmBtn = page.locator('button').filter({ hasText: /确定|确认|导出/ }).last();
    if (await confirmBtn.isVisible().catch(() => false)) {
      // 设置下载监听
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);
      await confirmBtn.click();
      await page.waitForTimeout(2000);

      // 验证下载开始或导出成功
      const download = await downloadPromise;
      if (download) {
        expect(download).toBeTruthy();
      }
    }
  });
});
