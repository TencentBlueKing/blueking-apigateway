// @generated from: test-bdd/cases/18-MCP服务/01-MCP服务管理.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  cleanupMcpServersByName,
  createTestMcpServer,
  createTestName,
  getGatewayId,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiGet,
  pageApiPatch,
  pageApiPut,
  unwrapApiData,
  unwrapApiResults,
} = require('../../runtime/helpers');

async function listMcpServers(page, gatewayId) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/`));
}

function isInactiveReleasedStageError(error) {
  return String(error && error.message || error).includes('环境已下架或者未发布');
}

test.describe('功能: MCP服务 - MCP Server管理', () => {
  test('场景: MCP Server 生命周期', async ({ page }, testInfo) => {
    const gatewayId = getGatewayId();
    const name = createTestName('bdd-mcp-life');
    const updatedTitle = `BDD MCP Updated ${name}`;
    let server;

    await navigateToGatewayPage(page, gatewayId, 'MCP Server', '/mcp/server');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/mcp/server`));

    try {
      let created;
      try {
        created = await createTestMcpServer(page, gatewayId, {
          name,
          title: `BDD MCP ${name}`,
          description: `BDD MCP Server ${name}`,
        });
      } catch (error) {
        if (isInactiveReleasedStageError(error)) {
          testInfo.annotations.push({
            type: 'backend-blocked',
            description: 'MCP Server creation requires an active released stage, but the BDD setup stage is inactive in this environment',
          });
          return;
        }
        throw error;
      }
      server = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${created.id}/`));

      let servers = await listMcpServers(page, gatewayId);
      expect(servers.some(item => item.name === name)).toBe(true);

      const resourceNames = server.resource_names || server.tools?.map(item => item.name) || [];
      const toolNames = server.tool_names || server.tools?.map(item => item.tool_name || item.name) || resourceNames;
      expect(resourceNames.length).toBeGreaterThan(0);

      await pageApiPut(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`, {
        title: updatedTitle,
        description: `Updated ${server.description}`,
        is_public: true,
        labels: [],
        resource_names: resourceNames,
        tool_names: toolNames,
        prompts: [],
        protocol_type: server.protocol_type || 'sse',
        category_ids: [],
        oauth2_public_client_enabled: false,
        raw_response_enabled: false,
      });

      server = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`));
      expect(server.title).toBe(updatedTitle);

      await pageApiPatch(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/status/`, { status: 0 });
      server = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`));
      expect(Number(server.status)).toBe(0);

      await pageApiPatch(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/status/`, { status: 1 });
      server = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`));
      expect(Number(server.status)).toBe(1);

      await pageApiPatch(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/status/`, { status: 0 });
      server = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`));
      expect(Number(server.status)).toBe(0);

      await pageApiDelete(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`);
      server = null;

      servers = await listMcpServers(page, gatewayId);
      expect(servers.some(item => item.name === name)).toBe(false);
    } finally {
      if (server) {
        await cleanupMcpServersByName(page, gatewayId, name);
      }
    }
  });
});
