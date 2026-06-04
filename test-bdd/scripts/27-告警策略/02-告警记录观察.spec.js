// @generated from: test-bdd/cases/27-告警策略/02-告警记录观察.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  getGatewayId,
  navigateToGatewayPage,
  pageApiGet,
  unwrapApiResults,
} = require('../../runtime/helpers');

test.describe('功能: 告警策略 - 告警记录观察', () => {
  test('场景: 观察告警记录列表', async ({ page }) => {
    const gatewayId = getGatewayId();

    await navigateToGatewayPage(page, gatewayId, '告警记录', '/monitor/alarm-history');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/monitor/alarm-history`));

    const historyResponse = await pageApiGet(page, `/gateways/${gatewayId}/monitors/alarm/records/`);
    unwrapApiResults(historyResponse);

    const content = page.locator('.bk-table, .bk-exception, [class*="empty"], [class*="history"]').first();
    await expect(content).toBeVisible({ timeout: 10000 });

    const filterInput = page.locator('input[placeholder*="筛选"], input[placeholder*="搜索"], .bk-search-select').first();
    if (await filterInput.isVisible({ timeout: 2000 })) {
      await filterInput.click();
      await page.keyboard.type('bdd');
      await page.keyboard.press('Enter');
    }
  });
});
