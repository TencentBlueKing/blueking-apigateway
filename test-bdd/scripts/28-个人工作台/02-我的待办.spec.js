// @generated from: test-bdd/cases/28-个人工作台/02-我的待办.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const { BASE_URL, pageApiGet, unwrapApiResults, waitForPageReady } = require('../../runtime/helpers');

test.describe('功能: 个人工作台 - 我的待办', () => {
  test('场景: 查看我的待办', async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/personal-workbench/my-pending`, { waitUntil: 'domcontentloaded' });
    await waitForPageReady(page);
    await expect(page).toHaveURL(/\/personal-workbench\/my-pending/);

    const gatewayResponse = await pageApiGet(page, '/me/workbench/permissions/gateway/pending/');
    const mcpResponse = await pageApiGet(page, '/me/workbench/permissions/mcp/pending/');
    expect(Array.isArray(unwrapApiResults(gatewayResponse))).toBe(true);
    expect(Array.isArray(unwrapApiResults(mcpResponse))).toBe(true);

    await expect(page.locator('.bk-tab, [class*="tab"], body').filter({ hasText: /网关|API/ }).first()).toBeVisible();
    await expect(page.locator('.bk-tab, [class*="tab"], body').filter({ hasText: /MCP/ }).first()).toBeVisible();

    const content = page.locator('.bk-table, .bk-exception, [class*="empty"], [class*="table"]').first();
    await expect(content).toBeVisible({ timeout: 10000 });
  });
});
