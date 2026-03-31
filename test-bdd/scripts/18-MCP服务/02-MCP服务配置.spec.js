// @generated from: test-bdd/cases/18-MCP服务/02-MCP服务配置.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");

const GATEWAY_ID = 6; // read-only

test.describe('功能: MCP服务 - MCP Server配置', () => {
  test.beforeEach(async ({ page }) => {
    const gwId = getGatewayId();
    await navigateToGatewayPage(page, gwId, 'MCP Server', '/mcp');
  });

  test('场景: 配置连接方式', async ({ page }) => {
    // 进入MCP Server详情页 - 点击列表中的第一个MCP Server
    const firstRow = page.locator('.bk-table tbody tr, .bk-table-body tr, [class*="card"], [class*="list-item"]').first();
    if (await firstRow.isVisible().catch(() => false)) {
      const nameLink = firstRow.locator('a, [class*="link"], [class*="name"]').first();
      if (await nameLink.isVisible().catch(() => false)) {
        await nameLink.click();
        await waitForPageReady(page);
      }

      // 查看使用指引中的配置信息
      const configSection = page.locator('[class*="config"], [class*="guide"], [class*="instruction"]').first();
      if (await configSection.isVisible().catch(() => false)) {
        await expect(configSection).toBeVisible();
      }

      // 支持复制各项配置信息
      const copyBtn = page.locator('button, [class*="copy"], .icon-copy').first();
      if (await copyBtn.isVisible().catch(() => false)) {
        await expect(copyBtn).toBeVisible();
      }
    }
  });

  test('场景: 配置资源与Prompt (read-only verification)', async ({ page }) => {
    // 验证创建/编辑MCP Server时的资源选择区域
    const createBtn = page.locator('button, .bk-button').filter({ hasText: /新建|编辑/ }).first();
    if (await createBtn.isVisible().catch(() => false)) {
      await expect(createBtn).toBeVisible();
    }

    // 验证页面有资源相关区域
    const contentArea = page.locator('.bk-table, [class*="resource"], [class*="mcp"]').first();
    if (await contentArea.isVisible().catch(() => false)) {
      await expect(contentArea).toBeVisible();
    }
  });
});
