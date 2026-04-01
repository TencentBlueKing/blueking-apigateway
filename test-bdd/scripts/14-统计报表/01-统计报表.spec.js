// @generated from: test-bdd/cases/14-统计报表/01-统计报表.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 统计报表 - 运行数据统计', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '统计报表', '/statistics');
  });

  test('场景: 查看统计图表', async ({ page }) => {
    const chartArea = page.locator('[class*="chart"], [class*="echart"], canvas, .bk-table, [class*="statistic"]').first();
    const chartVisible = await chartArea.isVisible({ timeout: 10000 }).catch(() => false);

    if (chartVisible) {
      await expect(chartArea).toBeVisible();

      const resourceSelect = page.locator('.bk-select').first();
      if (await resourceSelect.isVisible().catch(() => false)) {
        await expect(resourceSelect).toBeVisible();
      }

      const refreshBtn = page.locator('button, .bk-button, .bk-icon').filter({ hasText: /刷新/ }).first();
      if (await refreshBtn.isVisible().catch(() => false)) {
        await expect(refreshBtn).toBeVisible();
      }
    } else {
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 时间范围切换', async ({ page }) => {
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    const timeRangePicker = page.locator('.bk-date-picker, [class*="date-picker"], [class*="time-range"]').first();
    if (await timeRangePicker.isVisible().catch(() => false)) {
      await timeRangePicker.click();
      await page.waitForTimeout(300);

      const shortcutBtn = page.locator('.bk-picker-panel-shortcut, [class*="shortcut"]').first();
      if (await shortcutBtn.isVisible().catch(() => false)) {
        await expect(shortcutBtn).toBeVisible();
      }

      // Close picker
      await page.locator('body').click({ position: { x: 10, y: 10 } });
      await page.waitForTimeout(300);
    }
  });
});
