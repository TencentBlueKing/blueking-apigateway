// @generated from: test-bdd/cases/01-网关管理/02-网关列表操作.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, readRuntimeState, getGatewayListItemByText, selectDropdownOption } = require('../../runtime/helpers');
const name = () => process.env.TEST_GATEWAY_NAME || readRuntimeState().TEST_GATEWAY_NAME;

async function search(page, keyword) {
  const [response] = await Promise.all([
    page.waitForResponse(r => {
      const url = new URL(r.url());
      return url.pathname === '/backend/gateways/' && url.searchParams.get('keyword') === keyword;
    }),
    page.getByPlaceholder('请输入网关名称', { exact: true }).fill(keyword),
  ]);
  expect(response.status()).toBe(200);
  return (await response.json()).data;
}

test.describe('功能: 网关管理 - 网关列表', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.getByPlaceholder('请输入网关名称', { exact: true })).toBeVisible();
  });
  test('场景: 搜索网关', async ({ page }) => {
    const found = await search(page, name());
    expect(found.results.some(g => String(g.id) === getGatewayId())).toBe(true);
    expect(found.results.every(g => g.name.includes(name()))).toBe(true);
    await expect(getGatewayListItemByText(page, name())).toBeVisible();
    const empty = await search(page, `bdd-no-gateway-${Date.now()}`);
    expect(empty.results).toEqual([]);
    expect(empty.count).toBe(0);
    await expect(page.locator('.table-container')).not.toContainText(name());
    await expect(page.locator('body')).toContainText(/搜索结果为空|暂无数据/);
  });
  test('场景: 查看网关详情', async ({ page }) => {
    await search(page, name());
    const row = getGatewayListItemByText(page, name());
    await row.getByRole('button', { name: '资源配置', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/resource/setting$`));
    await expect(page.locator('.content-view')).toContainText('资源名称');
    await page.goto(BASE_URL);
    await search(page, name());
    await getGatewayListItemByText(page, name()).getByRole('button', { name: '环境概览', exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/stage/overview$`));
    await expect(page.locator('.content-view')).toContainText('prod');
    await page.goto(BASE_URL);
    await expect(page.getByPlaceholder('请输入网关名称', { exact: true })).toBeVisible();
    const [filtered] = await Promise.all([
      page.waitForResponse(r => new URL(r.url()).pathname === '/backend/gateways/' && new URL(r.url()).searchParams.get('kind') === '0'),
      (async () => { expect(await selectDropdownOption(page, page.locator('.home-container .bk-select').first(), '普通网关')).toBe(true); })(),
    ]);
    expect(filtered.status()).toBe(200);
    const data = (await filtered.json()).data;
    expect(data.results.every(g => Number(g.kind) === 0)).toBe(true);
  });
});
