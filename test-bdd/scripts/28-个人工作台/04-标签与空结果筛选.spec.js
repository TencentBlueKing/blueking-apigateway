// @generated from: test-bdd/cases/28-个人工作台/04-标签与空结果筛选.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, waitForBackendRequests } = require('../../runtime/helpers');

test.describe('功能: 个人工作台 - 标签与空结果筛选', () => {
  for (const [route, status] of [['my-apply', 'applied'], ['my-pending', 'pending'], ['my-handled', 'handled']]) {
    for (const [kind, label] of [['gateway', 'API 网关'], ['mcp', 'MCP Server']]) {
      test(`场景: ${route} - ${label}筛选无结果`, async ({ page }) => {
        await page.goto(`${BASE_URL.replace(/\/$/, '')}/personal-workbench/${route}`);
        const tabs = page.locator('.personal-workbench-top-bar');
        await expect(tabs).toBeVisible();
        await tabs.getByText(label, { exact: true }).click();
        await waitForBackendRequests(page);
        const keyword = `bdd-no-such-app-${Date.now()}`;
        const input = page.getByPlaceholder('请输入应用ID', { exact: true });
        const [response] = await Promise.all([
          page.waitForResponse(r => {
            const url = new URL(r.url());
            return url.pathname.endsWith(`/permissions/${kind}/${status}/`)
              && url.searchParams.get('bk_app_code') === keyword;
          }),
          (async () => { await input.fill(keyword); await input.press('Enter'); })(),
        ]);
        expect(response.status(), await response.text()).toBe(200);
        const data = (await response.json()).data;
        expect(data.results).toEqual([]);
        expect(data.count).toBe(0);
        await expect(page.locator('body')).toContainText('搜索结果为空');
        // Clear filter must issue a new unfiltered request, not leave stale empty data.
        const [cleared] = await Promise.all([
          page.waitForResponse(r => {
            const url = new URL(r.url());
            return url.pathname.endsWith(`/permissions/${kind}/${status}/`) && !url.searchParams.get('bk_app_code');
          }),
          (async () => { await input.fill(''); await input.press('Enter'); })(),
        ]);
        expect(cleared.status()).toBe(200);
        expect(Array.isArray((await cleared.json()).data.results)).toBe(true);
      });
    }
  }
});
