// @generated from: test-bdd/cases/26-MCP市场/02-搜索与详情.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, pageApiGet, unwrapApiResults } = require('../../runtime/helpers');

test.describe('功能: MCP市场 - 搜索与详情', () => {
  test('场景: 搜索不存在的MCP并清空条件', async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/mcp-market`);
    const input = page.getByPlaceholder('搜索 MCP 名称、展示名、描述');
    const keyword = `bdd-no-such-mcp-${Date.now()}`;
    const [response] = await Promise.all([
      page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/mcp-marketplace/servers/')
        && new URL(r.url()).searchParams.get('keyword') === keyword),
      input.fill(keyword),
    ]);
    expect(response.status()).toBe(200);
    expect((await response.json()).data.results).toEqual([]);
    await expect(page.locator('.mcp-market-list')).toContainText('搜索结果为空');
    const [cleared] = await Promise.all([
      page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/mcp-marketplace/servers/')
        && !new URL(r.url()).searchParams.get('keyword')),
      input.fill(''),
    ]);
    expect(cleared.status()).toBe(200);
    expect(Array.isArray((await cleared.json()).data.results)).toBe(true);
  });

  test('场景: 已公开MCP详情与刷新', async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/mcp-market`);
    const servers = unwrapApiResults(await pageApiGet(page, '/mcp-marketplace/servers/', { limit: 1 }));
    test.skip(!servers.length, '环境中没有公开 MCP，详情路径缺少前置数据');
    const server = servers[0];
    const url = `${BASE_URL.replace(/\/$/, '')}/mcp-market-details/${server.id}`;
    await page.goto(url);
    await expect(page.locator('.mcp-market-detail-wrapper')).toContainText(server.name);
    await expect(page.locator('.mcp-market-detail-wrapper')).toContainText('可用工具');
    await page.reload();
    await expect(page.locator('.mcp-market-detail-wrapper')).toContainText(server.name);
  });
});
