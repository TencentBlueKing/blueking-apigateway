// @generated from: test-bdd/cases/02-资源配置/02-编辑资源.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, pageApiGet, pageApiDelete, unwrapApiData } = require('../../runtime/helpers');
const { createOwnedResource } = require('../../runtime/test-data');

test.describe('功能: 资源配置 - 编辑资源', () => {
  let resource;
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    resource = await createOwnedResource(page, getGatewayId());
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/edit/${resource.id}`);
    await expect(page.locator('input[placeholder*="字母"]').first()).toHaveValue(resource.name);
  });
  test.afterEach(async ({ page }) => {
    if (resource) await pageApiDelete(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`);
    resource = undefined;
  });

  test('场景: 编辑基础信息', async ({ page }) => {
    const description = `BDD edited ${resource.name}`;
    await page.getByPlaceholder('请输入描述', { exact: true }).first().fill(description);
    const saved = page.waitForResponse(r => r.url().endsWith(`/resources/${resource.id}/`) && r.request().method() === 'PUT');
    await page.getByRole('button', { name: '提交', exact: true }).click();
    const response = await saved;
    expect(response.ok(), await response.text()).toBe(true);
    const detail = unwrapApiData(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`));
    expect(detail.description).toBe(description);
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/edit/${resource.id}`);
    await expect(page.getByPlaceholder('请输入描述', { exact: true }).first()).toHaveValue(description);
  });

  test('场景: 编辑后端配置', async ({ page }) => {
    const backendPath = `/bdd_updated/${resource.name}/`;
    await page.locator('input[placeholder*="斜线"]').last().fill(backendPath);
    const saved = page.waitForResponse(r => r.url().endsWith(`/resources/${resource.id}/`) && r.request().method() === 'PUT');
    await page.getByRole('button', { name: '提交', exact: true }).click();
    const response = await saved;
    expect(response.ok(), await response.text()).toBe(true);
    const detail = unwrapApiData(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`));
    expect(detail.backend.config.path).toBe(backendPath);
  });
});
