// @generated from: test-bdd/cases/18-MCP服务/03-MCP服务可观测.md
// @generated-date: 2026-07-07

const { test, expect } = require('@playwright/test');
const {
  getGatewayId,
  navigateToGatewayPage,
} = require('../../runtime/helpers');

test.describe('功能: MCP服务 - MCP Server可观测', () => {
  test('场景: 查看 MCP Server 可观测页面', async ({ page }) => {
    const gatewayId = getGatewayId();

    await navigateToGatewayPage(page, gatewayId, '可观测', '/mcp/observability');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/mcp/observability`), { timeout: 10000 });

    const body = page.locator('body');
    await expect(body).toContainText(/流水日志|仪表盘/);

    const flowLogTab = page.locator('.bk-tab-header-item, .bk-tab-label-item, [role=tab]').filter({ hasText: '流水日志' }).first();
    await expect(flowLogTab).toBeVisible({ timeout: 10000 });
    await expect(body).toContainText(/查询|重置|搜索结果为空|暂无数据|请求/);

    const dashboardTab = page.locator('.bk-tab-header-item, .bk-tab-label-item, [role=tab]').filter({ hasText: '仪表盘' }).first();
    await expect(dashboardTab).toBeVisible({ timeout: 10000 });
    await dashboardTab.click();
    await page.waitForTimeout(800);
    await expect(body).toContainText(/仪表盘|请求数|健康率|暂无数据|搜索结果为空|Query|Request/);
  });
});
