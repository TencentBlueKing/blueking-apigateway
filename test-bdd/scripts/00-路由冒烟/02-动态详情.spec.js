// @generated from: test-bdd/cases/00-路由冒烟/02-动态详情.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const {
  BASE_URL, getGatewayId, pageApiGet, pageApiDelete, pageApiPatch, unwrapApiResults,
  createTestMcpServer, createTestName,
} = require('../../runtime/helpers');
const { createOwnedResource } = require('../../runtime/test-data');

const base = BASE_URL.replace(/\/$/, '');
test.describe('功能: 全站路由冒烟 - 动态详情', () => {
  test('场景: MCP管理详情深链接', async ({ page }) => {
    await page.goto(BASE_URL);
    const name = createTestName('bdd-route-mcp');
    const resource = await createOwnedResource(page, getGatewayId());
    let server;
    try {
      server = await createTestMcpServer(page, getGatewayId(), { name, resource });
      expect(server.id).toBeTruthy();
      await page.goto(`${base}/${getGatewayId()}/mcp/detail/${server.id}`);
      await expect(page.locator('.content-view')).toContainText(name);
      await expect(page.locator('.content-view')).toContainText('可用工具');
      await expect(page.locator('.content-view')).toContainText('使用指引');
    } finally {
      if (server?.id) {
        await pageApiPatch(page, `/gateways/${getGatewayId()}/mcp-servers/${server.id}/status/`, { status: 0 });
        await pageApiDelete(page, `/gateways/${getGatewayId()}/mcp-servers/${server.id}/`);
      }
      await pageApiDelete(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`);
    }
  });

  test('场景: 组件同步版本深链接', async ({ page }) => {
    await page.goto(BASE_URL);
    const histories = unwrapApiResults(await pageApiGet(page, '/esb/components/sync/release/histories/', { limit: 1 }));
    test.skip(!histories.length, '共享环境没有组件同步历史，缺少只读详情数据');
    expect(histories[0].id).toBeTruthy();
    await page.goto(`${base}/components/version?id=${histories[0].id}`);
    await expect(page.locator('body')).toContainText(/版本|同步/);
    await expect(page.locator('table')).toBeVisible();
  });

  test('场景: 系统实时概况深链接', async ({ page }) => {
    await page.goto(BASE_URL);
    const systems = unwrapApiResults(await pageApiGet(page, '/esb/status/systems/summary/', { time_since: '1h' }));
    test.skip(!systems.length, '共享环境没有运行数据，缺少只读详情数据');
    const name = systems[0].name || systems[0].system_name || systems[0].system;
    expect(name).toBeTruthy();
    await page.goto(`${base}/components/system/${encodeURIComponent(name)}/detail`);
    await expect(page.locator('body')).toContainText(name);
    await expect(page.locator('body')).toContainText(/请求|响应|耗时/);
  });
});
