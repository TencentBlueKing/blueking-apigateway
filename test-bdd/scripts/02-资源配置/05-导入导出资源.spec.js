// @generated from: test-bdd/cases/02-资源配置/05-导入导出资源.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, createTestIdentifier, pageApiGet, pageApiDelete, unwrapApiResults, getTableRowByText } = require('../../runtime/helpers');
const { createOwnedResource } = require('../../runtime/test-data');
const template = require('../../fixtures/resource-openapi.json');

async function importPage(page) {
  await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/import`);
  await expect(page.locator('input[type=file]')).toBeAttached();
}
async function downloadText(download) {
  expect(await download.failure(), 'Download must complete successfully').toBeNull();
  const stream = await download.createReadStream();
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

test.describe('功能: 资源配置 - 导入导出资源', () => {
  test('场景: 导入资源', async ({ page }) => {
    const name = createTestIdentifier('bdd_import');
    const document = structuredClone(template);
    const operation = document.paths['/bdd_import/'].get;
    operation.operationId = name;
    document.paths = { [`/bdd/${name}/`]: { get: operation } };
    await importPage(page);
    await page.locator('input[type=file]').setInputFiles({ name: 'bdd-openapi.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(document)) });
    await expect(page.getByRole('button', { name: '下一步', exact: true })).toBeEnabled();
    await page.getByRole('button', { name: '下一步', exact: true }).click();
    await expect(page.locator('.imported-resources-wrap')).toContainText(name);
    await page.getByRole('button', { name: '确定导入', exact: true }).click();
    const result = page.waitForResponse(r => r.url().endsWith('/resources/import/') && r.request().method() === 'POST');
    await page.locator('.custom-main-dialog .dialog-footer').getByRole('button', { name: '确定导入', exact: true }).click();
    const response = await result;
    expect(response.ok(), await response.text()).toBe(true);
    await expect(page.locator('body')).toContainText(/成功导入\s*1\s*个资源/);
    const resources = unwrapApiResults(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/`, { name, limit: 100 }));
    const created = resources.find(r => r.name === name);
    expect(created).toBeTruthy();
    expect(created.path).toBe(`/bdd/${name}/`);
    expect(created.method).toBe('GET');
    const docs = unwrapApiResults(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/${created.id}/docs/`));
    expect(docs.length, 'Generate resource documentation is enabled by default').toBeGreaterThan(0);
  });

  test('场景: 无效OpenAPI文件阻止导入', async ({ page }) => {
    await importPage(page);
    await page.locator('input[type=file]').setInputFiles({ name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from('{"openapi":"3.0.1"}') });
    await expect(page.getByRole('button', { name: '下一步', exact: true })).toBeDisabled();
    await expect(page.locator('.editor-message').first()).toBeVisible();
    await expect(page.locator('.editor-message').first()).not.toHaveText('');
    await expect(page.getByRole('button', { name: '确定导入', exact: true })).toHaveCount(0);
  });

  for (const format of ['JSON', 'YAML']) {
    test(`场景: 导出全部资源 - ${format}`, async ({ page }) => {
      await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/setting`);
      const resources = unwrapApiResults(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/`, { limit: 10000 }));
      expect(resources.length).toBeGreaterThan(0);
      await page.locator('button').filter({ hasText: /^导出/ }).first().click();
      await page.getByText('全部资源', { exact: true }).click();
      const dialog = page.locator('.export-resource-dialog');
      await dialog.getByText(`${format}格式`, { exact: true }).click();
      const pending = page.waitForEvent('download');
      await dialog.getByRole('button', { name: '确定', exact: true }).click();
      const download = await pending;
      const content = await downloadText(download);
      expect(content.length).toBeGreaterThan(0);
      for (const resource of resources) expect(content).toContain(resource.name);
      if (format === 'JSON') {
        const exported = JSON.parse(content);
        expect(exported.openapi || exported.swagger).toBeTruthy();
        const names = Object.values(exported.paths).flatMap(methods => Object.values(methods)
          .filter(operation => operation && typeof operation === 'object' && operation.operationId)
          .map(operation => operation.operationId));
        expect(names.sort()).toEqual(resources.map(r => r.name).sort());
      }
    });
  }

  for (const format of ['JSON', 'YAML']) {
    test(`场景: 仅导出已选资源 - ${format}`, async ({ page }) => {
      const resources = [];
      await page.goto(BASE_URL);
      try {
        for (let i = 0; i < 2; i++) resources.push(await createOwnedResource(page, getGatewayId()));
        await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/setting`);
        await page.getByRole('button', { name: '批量操作', exact: true }).click();
        for (const resource of resources) {
          const row = getTableRowByText(page, resource.name);
          await row.locator('.bk-checkbox-input').click();
          await expect(row.locator('input[type=checkbox]')).toBeChecked();
        }
        await page.locator('button:visible').filter({ hasText: /^导出/ }).click();
        await page.getByText('已选资源', { exact: true }).click();
        const dialog = page.locator('.export-resource-dialog');
        await expect(dialog).toContainText('已选择2个资源');
        await dialog.getByText(`${format}格式`, { exact: true }).click();
        const pending = page.waitForEvent('download');
        await dialog.getByRole('button', { name: '确定', exact: true }).click();
        const content = await downloadText(await pending);
        const names = format === 'JSON'
          ? Object.values(JSON.parse(content).paths).flatMap(methods => Object.values(methods)
            .filter(operation => operation?.operationId).map(operation => operation.operationId))
          : [...content.matchAll(/^\s*operationId:\s*['"]?([a-zA-Z0-9_]+)['"]?\s*$/gm)].map(match => match[1]);
        expect(names.sort()).toEqual(resources.map(resource => resource.name).sort());
      } finally {
        for (const resource of resources) await pageApiDelete(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`);
      }
    });
  }
});
