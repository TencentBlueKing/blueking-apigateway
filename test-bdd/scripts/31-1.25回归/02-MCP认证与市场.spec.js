// @generated from: test-bdd/cases/31-1.25回归/02-MCP认证与市场.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const {
  BASE_URL, getGatewayId, createTestMcpServer, createTestName, getActiveSideslider,
  pageApiGet, pageApiPatch, pageApiDelete, unwrapApiData,
} = require('../../runtime/helpers');
const base = BASE_URL.replace(/\/$/, '');

test.describe('功能: 1.25 MCP 认证配置与市场', () => {
  test('场景: 两种认证开关的四种组合保存后指引配置与市场图标一致', async ({ page }, testInfo) => {
    test.setTimeout(180000);
    await page.goto(BASE_URL);
    const gatewayId = getGatewayId();
    const name = createTestName('bdd125-mcp');
    let server;
    const results = [];
    try {
      server = await createTestMcpServer(page, gatewayId, { name });
      const api = `/gateways/${gatewayId}/mcp-servers/${server.id}/`;
      const categories = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/-/categories/`));
      expect(categories.length, '编辑表单要求有效分类').toBeGreaterThan(0);
      await pageApiPatch(page, api, { category_ids: [categories[0].id] });
      for (const [publicClient, personalClient] of [[true, true], [false, true], [true, false], [false, false]]) {
        await page.goto(`${base}/${gatewayId}/mcp/detail/${server.id}`);
        await expect(page.getByText('查看文档详情', { exact: true }).first()).toBeVisible();
        await page.getByRole('button', { name: '编辑', exact: true }).first().click();
        const slider = getActiveSideslider(page);
        await expect(slider.getByPlaceholder('请输入小写字母、数字、连字符(-)')).toHaveValue(name);
        await expect(slider).toContainText('已选1条');
        for (const [label, enabled] of [['OAuth2 公开客户端模式', publicClient], ['个人令牌', personalClient]]) {
          const toggle = slider.getByText(label, { exact: true }).locator('../../..').locator('.bk-switcher');
          const checked = (await toggle.getAttribute('class')).includes('is-checked');
          if (checked !== enabled) await toggle.click();
        }
        const saved = page.waitForResponse(r => r.url().endsWith(api) && r.request().method() === 'PATCH');
        await slider.getByRole('button', { name: /^(确定|已知晓风险并提交)$/ }).click();
        const response = await saved;
        expect(response.status(), await response.text()).toBe(204);
        await expect(slider).toBeHidden();
        await page.reload();
        const detail = unwrapApiData(await pageApiGet(page, api));
        expect(detail.oauth2_public_client_enabled).toBe(publicClient);
        expect(detail.oauth2_personal_client_enabled).toBe(personalClient);
        const guide = unwrapApiData(await pageApiGet(page, `${api}guideline/`)).content;
        expect(guide.includes('### OAuth2 公开客户端模式')).toBe(publicClient);
        expect(guide.includes('### 个人令牌')).toBe(personalClient);
        if (personalClient) expect(guide).toContain('Authorization: Bearer <your_personal_token>');
        const configs = unwrapApiData(await pageApiGet(page, `${api}configs/`)).configs;
        const jsonConfigs = configs.filter(config => config.name !== 'aidev');
        expect(jsonConfigs.map(config => config.name).sort()).toEqual(['claude', 'codebuddy', 'cursor', 'vscode']);
        for (const config of jsonConfigs) {
          const parsed = JSON.parse(config.content.match(/```json\s*([\s\S]*?)```/)[1]);
          const entry = (parsed.mcpServers || parsed.servers)[name];
          expect(entry.url).toBe(detail.url);
          if (publicClient) expect(entry.headers?.['X-Bkapi-Authorization']).toBeUndefined();
        }
        await page.getByText('使用指引', { exact: true }).click();
        if (personalClient) await expect(page.locator('.content-view')).toContainText('Authorization: Bearer <your_personal_token>');
        await page.goto(`${base}/mcp-market`);
        const filtered = page.waitForResponse(r => new URL(r.url()).pathname.endsWith('/mcp-marketplace/servers/')
          && new URL(r.url()).searchParams.get('keyword') === name);
        await page.getByPlaceholder('搜索 MCP 名称、展示名、描述').fill(name);
        expect((await filtered).status()).toBe(200);
        const card = page.locator('.ag-mcp-card-wrapper').filter({ hasText: name });
        await expect(card).toHaveCount(1);
        await expect(card.locator('.icon-ag-key-fill')).toHaveCount(personalClient ? 1 : 0);
        results.push({ publicClient, personalClient, configs: jsonConfigs.map(config => config.name) });
      }
      await testInfo.attach('authentication-combinations', { body: JSON.stringify(results), contentType: 'application/json' });
    } finally {
      if (server?.id) {
        await pageApiPatch(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/status/`, { status: 0 });
        await pageApiDelete(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`);
      }
    }
  });
});
