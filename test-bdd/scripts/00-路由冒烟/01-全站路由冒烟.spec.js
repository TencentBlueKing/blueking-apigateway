// @generated from: route inventory in src/dashboard-front/src/router/index.ts and src/views/*/route*.ts
// @generated-date: 2026-07-07

const { test, expect } = require('../../runtime/bdd-test');
const {
  BASE_URL,
  assertNoHardFailure,
  getGatewayId,
  pageApiGet,
  unwrapApiResults,
  waitForPageReadyAndAssert,
} = require('../../runtime/helpers');

const baseUrl = BASE_URL.replace(/\/$/, '');

function uniqueRoutes(routes) {
  const seen = new Set();
  return routes.filter((route) => {
    if (seen.has(route.path)) return false;
    seen.add(route.path);
    return true;
  });
}

async function gotoRoute(page, path, title) {
  await page.goto(`${baseUrl}${path}`, { waitUntil: 'domcontentloaded' });
  await waitForPageReadyAndAssert(page, title);
  await expect(page).toHaveURL(new RegExp(path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\\\/[^/]+/g, '\\/[^/]+')));
}

async function firstResult(page, path, query) {
  const response = await pageApiGet(page, path, query, { allowFailure: true });
  if (!response.ok) return null;
  return unwrapApiResults(response)[0] || null;
}

test.describe('功能: 全站路由冒烟 - 无 500 / 无失败页', () => {
  test.setTimeout(300000);

  test('场景: 访问所有静态页面和可解析动态页面', async ({ page }, testInfo) => {
    const gatewayId = getGatewayId();
    const routes = uniqueRoutes([
      { path: '/', title: '网关首页' },
      { path: `/${gatewayId}/stage/overview`, title: '环境概览' },
      { path: `/${gatewayId}/stage/release-record`, title: '发布记录' },
      { path: `/${gatewayId}/resource/setting`, title: '资源配置' },
      { path: `/${gatewayId}/resource/create`, title: '新建资源' },
      { path: `/${gatewayId}/resource/import`, title: '导入资源配置' },
      { path: `/${gatewayId}/resource/import-doc`, title: '导入资源文档' },
      { path: `/${gatewayId}/resource/version`, title: '资源版本' },
      { path: `/${gatewayId}/basic-info`, title: '基本信息' },
      { path: `/${gatewayId}/backend`, title: '后端服务' },
      { path: `/${gatewayId}/permission/apply`, title: '权限审批' },
      { path: `/${gatewayId}/permission/record`, title: '审批历史' },
      { path: `/${gatewayId}/permission/app`, title: '应用权限' },
      { path: `/${gatewayId}/log`, title: '流水日志' },
      { path: `/${gatewayId}/dashboard`, title: '仪表盘' },
      { path: `/${gatewayId}/report`, title: '统计报表' },
      { path: `/${gatewayId}/online-debugging`, title: '在线调试' },
      { path: `/${gatewayId}/audit`, title: '审计日志' },
      { path: `/${gatewayId}/monitor/alarm-strategy`, title: '告警策略' },
      { path: `/${gatewayId}/monitor/alarm-history`, title: '告警记录' },
      { path: `/${gatewayId}/mcp/server`, title: 'MCP Server' },
      { path: `/${gatewayId}/mcp/permission`, title: 'MCP 权限审批' },
      { path: `/${gatewayId}/mcp/observability`, title: 'MCP 可观测' },
      { path: '/platform-tools/toolbox', title: '工具箱' },
      { path: '/platform-tools/automated-gateway', title: '自动化接入网关' },
      { path: '/platform-tools/bk-cli', title: '平台工具 BK-CLI' },
      { path: '/platform-tools/programmable-gateway', title: '可编程网关' },
      { path: '/platform-tools/micro-gateway', title: '蓝鲸微网关' },
      { path: '/bk-cli', title: '独立 BK-CLI' },
      { path: '/components/intro', title: '组件简介' },
      { path: '/components/system', title: '系统管理' },
      { path: '/components/access', title: '组件管理' },
      { path: '/components/sync', title: '同步组件配置' },
      { path: '/components/history', title: '组件同步历史' },
      { path: '/components/category', title: '文档分类' },
      { path: '/components/runtime-data', title: '实时运行数据' },
      { path: '/docs/api-docs', title: 'API 文档' },
      { path: '/docs/api-docs/gateway', title: '网关 API 文档' },
      { path: '/docs/api-docs/component', title: '组件 API 文档' },
      { path: '/mcp-market', title: 'MCP 市场' },
      { path: '/personal-workbench/my-apply', title: '我的申请' },
      { path: '/personal-workbench/my-pending', title: '我的待办' },
      { path: '/personal-workbench/my-handled', title: '我的已办' },
    ]);

    await gotoRoute(page, '/', '网关首页');

    const resource = await firstResult(page, `/gateways/${gatewayId}/resources/`, { limit: 1, offset: 0 });
    if (resource) {
      routes.push({ path: `/${gatewayId}/resource/edit/${resource.id}`, title: '编辑资源' });
      routes.push({ path: `/${gatewayId}/resource/clone/${resource.id}`, title: '克隆资源' });
    } else {
      testInfo.annotations.push({ type: 'route-smoke-unresolved', description: 'No resource available for resource edit/clone routes' });
    }

    const mcpServer = await firstResult(page, `/gateways/${gatewayId}/mcp-servers/`, { limit: 1, offset: 0 });
    if (mcpServer) {
      routes.push({ path: `/${gatewayId}/mcp/detail/${mcpServer.id}`, title: 'MCP Server 详情' });
    } else {
      testInfo.annotations.push({ type: 'route-smoke-unresolved', description: 'No MCP server available for MCP detail route' });
    }

    const syncHistory = await firstResult(page, '/esb/components/sync/release/histories/', { limit: 1, offset: 0 });
    if (syncHistory && syncHistory.id) {
      routes.push({ path: `/components/version?id=${syncHistory.id}`, title: '组件同步版本' });
    } else {
      testInfo.annotations.push({ type: 'route-smoke-unresolved', description: 'No component sync history available for sync version route' });
    }

    const componentSystem = await firstResult(page, '/esb/status/systems/summary/', { time_since: '1h' });
    const systemName = componentSystem && (componentSystem.name || componentSystem.system_name || componentSystem.system);
    if (systemName) {
      routes.push({ path: `/components/system/${encodeURIComponent(systemName)}/detail`, title: '系统实时概况' });
    } else {
      testInfo.annotations.push({ type: 'route-smoke-unresolved', description: 'No component runtime system available for system detail route' });
    }

    const mcpMarketServer = await firstResult(page, '/mcp-marketplace/servers/', { limit: 1, offset: 0 });
    if (mcpMarketServer) {
      routes.push({ path: `/mcp-market-details/${mcpMarketServer.id}`, title: 'MCP 市场详情' });
    } else {
      testInfo.annotations.push({ type: 'route-smoke-unresolved', description: 'No MCP marketplace server available for market detail route' });
    }

    for (const route of uniqueRoutes(routes).filter(item => item.path !== '/')) {
      await test.step(route.title, async () => {
        await gotoRoute(page, route.path, route.title);
        await expect(page.locator('body')).not.toContainText(/Server Error|Internal Server Error|OperationalError|Traceback|Bad Gateway|Service Unavailable|Gateway Timeout|系统出现异常|努力恢复中|请稍后再试|页面找不到|404 page|page not found/i);
        await assertNoHardFailure(page, route.title);
      });
    }
  });
});
