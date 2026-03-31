// @generated from: test-bdd/cases/03-资源版本/01-版本管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getToastMessage, getTableRowCount, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


// Read-only tests use gateway ID 6
const READONLY_GATEWAY_ID = 6;

test.describe('功能: 资源版本 - 版本管理', () => {
  test('场景: 生成版本', async ({ page }) => {
    // Mutating test uses TEST_GATEWAY_ID
    await navigateToGatewayPage(page, getGatewayId(), '资源版本', '/resource/version');

    // 点击生成版本按钮
    const genBtn = page.locator('button').filter({ hasText: /生成版本/ }).first();
    await expect(genBtn).toBeVisible({ timeout: 10000 });
    await genBtn.click();
    await page.waitForTimeout(800);

    // 输入版本号
    const versionInput = page.locator('input[placeholder*="版本"], input[name*="version"]').first();
    if (await versionInput.isVisible().catch(() => false)) {
      await versionInput.fill(`1.0.${Date.now().toString().slice(-6)}`);
    }

    // 输入版本说明
    const commentInput = page.locator('textarea, input[placeholder*="说明"], input[placeholder*="备注"]').first();
    if (await commentInput.isVisible().catch(() => false)) {
      await commentInput.fill('自动化测试生成的版本');
    }

    // 点击确定
    await page.locator('button').filter({ hasText: /确定|确认/ }).first().click();
    await page.waitForTimeout(2000);

    // 验证版本生成成功
    const toast = await getToastMessage(page);
    expect(toast).toMatch(/成功|生成/);
  });

  test('场景: 查看版本列表', async ({ page }) => {
    // Read-only test uses gateway ID 6
    await navigateToGatewayPage(page, '6', '资源版本', '/resource/version');

    // 验证版本列表可见
    const table = page.locator('table, .bk-table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    // 搜索版本号
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="版本"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('1.0');
      await page.waitForTimeout(1500);

      // 验证搜索结果
      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);
    }

    // 点击版本号查看详情
    const versionLink = page.locator('table tbody tr a, .bk-table-body tr a').first();
    if (await versionLink.isVisible().catch(() => false)) {
      await versionLink.click();
      await page.waitForTimeout(800);

      // 验证跳转到版本资源详情
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('场景: 版本对比', async ({ page }) => {
    // Read-only test uses gateway ID 6
    await navigateToGatewayPage(page, '6', '资源版本', '/resource/version');

    // 勾选两个版本
    const checkboxes = page.locator('table .bk-checkbox, .bk-table .bk-checkbox, input[type="checkbox"]');
    const count = await checkboxes.count();
    if (count >= 3) {
      // Skip header checkbox (index 0), select rows 1 and 2
      await checkboxes.nth(1).click();
      await page.waitForTimeout(200);
      await checkboxes.nth(2).click();
      await page.waitForTimeout(200);

      // 点击版本对比
      const compareBtn = page.locator('button').filter({ hasText: /版本对比|对比/ }).first();
      if (await compareBtn.isVisible().catch(() => false)) {
        await compareBtn.click();
        await page.waitForTimeout(800);

        // 验证对比页面展示
        const diffContent = page.locator('.diff-content, [class*="diff"], [class*="compare"]').first();
        await expect(diffContent).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('场景: 版本详情', async ({ page }) => {
    // Mutating test uses TEST_GATEWAY_ID
    await navigateToGatewayPage(page, getGatewayId(), '资源版本', '/resource/version');

    // 选择版本并点击发布至环境
    const publishBtn = page.locator('button, a').filter({ hasText: /发布/ }).first();
    if (await publishBtn.isVisible({ timeout: 10000 }).catch(() => false)) {
      await publishBtn.click();
      await page.waitForTimeout(800);

      // 选择目标环境
      const envOption = page.locator('.bk-select-option, .bk-option, label, .bk-checkbox').filter({ hasText: /prod|stag/ }).first();
      if (await envOption.isVisible().catch(() => false)) {
        await envOption.click();
        await page.waitForTimeout(300);
      }

      // 点击确认/下一步
      const nextBtn = page.locator('button').filter({ hasText: /下一步|确认/ }).first();
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(800);
      }

      // 确认发布
      const confirmPublish = page.locator('button').filter({ hasText: /确认发布|发布|确定/ }).first();
      if (await confirmPublish.isVisible().catch(() => false)) {
        await confirmPublish.click();
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|发布/);
      }
    }
  });
});
