// @generated from: test-bdd/cases/24-API文档/01-API文档.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, pageApiGet, unwrapApiResults, getActiveSideslider } = require('../../runtime/helpers');
const base = BASE_URL.replace(/\/$/, '');

test.describe('功能: API文档 - API文档查看', () => {
  test('场景: 搜索网关API文档', async ({ page }) => {
    await page.goto(`${base}/docs/api-docs/gateway`);
    const input = page.getByPlaceholder('请输入网关名称或描述');
    const keyword = `bdd-no-such-gateway-${Date.now()}`;
    const [response] = await Promise.all([
      page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/docs/gateways/')
        && new URL(r.url()).searchParams.get('keyword') === keyword),
      input.fill(keyword),
    ]);
    expect(response.status()).toBe(200);
    expect((await response.json()).data.results).toEqual([]);
    await expect(page.locator('body')).toContainText('搜索结果为空');
    await input.fill('');
    const gateways = unwrapApiResults(await pageApiGet(page, '/docs/gateways/', { limit: 1 }));
    test.skip(!gateways.length, '没有公开网关文档，无法验证动态详情');
    const gateway = gateways[0];
    await input.fill(gateway.name);
    const row = page.locator('table tbody tr').filter({ hasText: gateway.name }).first();
    await row.getByText(gateway.name, { exact: true }).click();
    await expect.poll(() => new URL(page.url()).pathname).toBe(`/docs/api-docs/gateway/${gateway.name}`);
    await expect(page.locator('.page-wrap .page-content')).toContainText(/API地址|暂无数据|未发布/);
  });
  test('场景: 查看组件API文档', async ({ page }) => {
    await page.goto(`${base}/docs/api-docs/component`);
    const first = page.locator('.group-items .item').first();
    await expect(first).toBeVisible();
    const name = (await first.locator('.name-en').innerText()).trim();
    await first.click();
    await expect(page).toHaveURL(new RegExp(`/docs/api-docs/component/[^/]+/${name}`));
    await expect(page.locator('.page-wrap')).toContainText(name);
    await expect(page.locator('.page-content')).toContainText(/API地址|暂无数据/);
  });
  test('场景: 查看SDK文档', async ({ page }) => {
    await page.goto(`${base}/docs/api-docs/gateway`);
    const row = page.locator('table tbody tr').first();
    await expect(row.getByRole('button', { name: '查看 SDK', exact: true })).toBeVisible();
    await row.getByRole('button', { name: '查看 SDK', exact: true }).click();
    const detail = getActiveSideslider(page);
    await expect(detail).toContainText('SDK包名称');
    await expect(detail).toContainText('SDK版本');
    await expect(detail).toContainText('安装');
    await expect(detail).toContainText('SDK 文档');
  });
});
