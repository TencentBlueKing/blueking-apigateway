// @generated from: test-bdd/cases/00-路由冒烟/02-动态详情.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const {
  BASE_URL, getGatewayId, pageApiDelete, pageApiPatch,
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
});
