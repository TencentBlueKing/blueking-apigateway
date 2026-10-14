// @generated from: test-bdd/cases/31-1.25回归/05-日志分享异常.md
// @generated-date: 2026-10-14
const { randomUUID } = require('node:crypto');
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, pageApiGet, unwrapApiData } = require('../../runtime/helpers');

test.describe('功能: 1.25 日志分享异常处理', () => {
  test('场景: 分享的日志不存在时展示明确空结果', async ({ page }, testInfo) => {
    await page.goto(BASE_URL);
    const gatewayId = getGatewayId();
    const requestId = randomUUID();
    const share = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/logs/${requestId}/link/`));
    const response = page.waitForResponse(r => new URL(r.url()).pathname === `/backend/gateways/${gatewayId}/logs/${requestId}/`);
    await page.goto(share.link);
    const result = await response;
    expect(result.status()).toBe(200);
    const data = (await result.json()).data;
    expect(data.results).toEqual([]);
    await testInfo.attach('empty-shared-log-result', {
      body: JSON.stringify({ gatewayId, requestId, count: data.count, results: data.results }),
      contentType: 'application/json',
    });
    await expect(page.getByText('请求时间', { exact: true })).toBeVisible();
    await expect(page.locator('body')).not.toContainText('Invalid Date');
    await expect(page.locator('body')).toContainText(/未找到.*日志|日志.*不存在|暂无数据/);
  });
});
