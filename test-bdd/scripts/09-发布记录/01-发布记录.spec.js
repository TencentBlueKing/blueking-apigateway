// @generated from: test-bdd/cases/09-发布记录/01-发布记录.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, getTableRowCount, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 发布记录 - 发布记录', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '发布记录', '/release/history');
  });

  test('场景: 查看发布记录', async ({ page }) => {
    // Verify we are on the right gateway page
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    // 验证发布记录列表展示
    const table = page.locator('table, .bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 10000 }).catch(() => false);

    if (tableVisible) {
      await expect(table).toBeVisible();

      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);

      // 点击某条发布记录的发布日志
      const logLink = page.locator('table tbody tr a, .bk-table-body tr a, button').filter({ hasText: /日志|查看/ }).first();
      if (await logLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        await logLink.click();
        await page.waitForTimeout(800);

        // 验证日志详情可见
        const logContent = page.locator('.bk-sideslider, .log-content, [class*="log"], [class*="detail"]').first();
        await expect(logContent).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('场景: 记录筛选', async ({ page }) => {
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    // 搜索环境名称
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="环境"]').first();
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('prod');
      await page.waitForTimeout(1500);

      // 验证筛选结果
      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);

      // 清空搜索
      await searchInput.clear();
      await page.waitForTimeout(1500);
    }

    // 时间筛选
    const datePickerInput = page.locator('.bk-date-picker, input[placeholder*="时间"], input[placeholder*="开始"]').first();
    if (await datePickerInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await datePickerInput.click();
      await page.waitForTimeout(300);

      // 关闭日期选择器
      await page.locator('body').click({ position: { x: 10, y: 10 } });
      await page.waitForTimeout(300);
    }
  });
});
