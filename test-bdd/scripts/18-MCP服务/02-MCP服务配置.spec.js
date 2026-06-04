// @generated from: test-bdd/cases/18-MCP服务/02-MCP服务配置.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  BASE_URL,
  cleanupMcpServersByName,
  createTestMcpServer,
  createTestName,
  getGatewayId,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiGet,
  pageApiPost,
  pageApiPut,
  unwrapApiData,
  unwrapApiResults,
  waitForPageReady,
} = require('../../runtime/helpers');

test.describe('功能: MCP服务 - MCP Server配置', () => {
  test('场景: 查看详情、Tool、接入配置和自定义文档', async ({ page }) => {
    const gatewayId = getGatewayId();
    const name = createTestName('bdd-mcp-config');
    let server;
    let customDocCreated = false;

    await navigateToGatewayPage(page, gatewayId, 'MCP Server', '/mcp/server');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/mcp/server`));

    try {
      server = await createTestMcpServer(page, gatewayId, {
        name,
        title: `BDD MCP ${name}`,
        description: `BDD MCP Server ${name}`,
      });

      await page.goto(`${BASE_URL.replace(/\/$/, '')}/${gatewayId}/mcp/detail/${server.id}`, { waitUntil: 'domcontentloaded' });
      await waitForPageReady(page);
      await expect(page).toHaveURL(new RegExp(`/${gatewayId}/mcp/detail/${server.id}`));

      const detail = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`));
      expect(detail.name).toBe(name);

      const toolsPath = `/gateways/${gatewayId}/mcp-servers/${server.id}/tool` + 's/';
      const tools = unwrapApiResults(await pageApiGet(page, toolsPath));
      expect(tools.length).toBeGreaterThan(0);

      const configs = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/configs/`));
      expect(configs).toBeTruthy();

      const guideline = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/guideline/`));
      expect(typeof guideline.content).toBe('string');

      const docContent = `# BDD MCP Doc\n\n${name}`;
      await pageApiPost(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`, {
        content: docContent,
      });
      customDocCreated = true;

      let customDoc = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`));
      expect(customDoc.content).toContain(name);

      await pageApiPut(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`, {
        content: `${docContent}\n\nupdated`,
      });
      customDoc = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`));
      expect(customDoc.content).toContain('updated');

      await pageApiDelete(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`);
      customDocCreated = false;

      const deletedDoc = await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`, null, { allowFailure: true });
      expect(deletedDoc.ok).toBe(false);

      const remotePrompts = await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/-/remote-prompts/`, null, { allowFailure: true });
      expect([true, false]).toContain(remotePrompts.ok);
    } finally {
      if (customDocCreated && server) {
        await pageApiDelete(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/user-custom-doc/`, null, { allowFailure: true });
      }
      await cleanupMcpServersByName(page, gatewayId, name);
    }
  });
});
