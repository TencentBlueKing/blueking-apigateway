// @generated from: test-bdd/cases/02-资源配置/01-创建资源.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, createTestIdentifier, pageApiGet, unwrapApiResults, selectDropdownOption } = require('../../runtime/helpers');

test.describe('功能: 资源配置 - 创建资源', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/create`);
    await expect(page.getByRole('button', { name: '提交', exact: true })).toBeVisible();
  });

  test('场景: 创建资源并配置后端', async ({ page }) => {
    const name = createTestIdentifier('bdd_create');
    await page.locator('input[placeholder*="字母"]').first().fill(name);
    await page.getByPlaceholder('请输入描述', { exact: true }).first().fill('BDD create persistence');
    const paths = page.locator('input[placeholder*="斜线"]');
    await expect(paths).toHaveCount(2);
    await paths.first().fill(`/bdd/${name}/`);
    await paths.last().fill('/get');
    expect(await selectDropdownOption(page, page.getByPlaceholder('请选择服务', { exact: true }), 'default')).toBe(true);
    const responsePromise = page.waitForResponse(r => r.url().endsWith(`/gateways/${getGatewayId()}/resources/`) && r.request().method() === 'POST');
    await page.getByRole('button', { name: '提交', exact: true }).click();
    const response = await responsePromise;
    expect(response.status(), await response.text()).toBe(201);
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/resource/setting$`));
    const rows = unwrapApiResults(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/`, { name, limit: 100 }));
    const created = rows.find(r => r.name === name);
    expect(created, 'UI submission must persist the resource').toBeTruthy();
    expect(created.path).toBe(`/bdd/${name}/`);
  });

  test('场景: 名称校验', async ({ page }) => {
    const form = page.locator('.content-view');
    await page.getByRole('button', { name: '提交', exact: true }).click();
    await expect(form.locator('.bk-form-error').filter({ hasText: /名称/ })).toBeVisible();
    await page.locator('input[placeholder*="字母"]').first().fill('invalid-name-#$%');
    await page.getByRole('button', { name: '提交', exact: true }).click();
    await expect(form.locator('.bk-form-error').filter({ hasText: /字母|名称/ }).first()).toBeVisible();
    await expect(page).toHaveURL(new RegExp('/resource/create$'));
  });

  test('场景: 请求配置', async ({ page }) => {
    await page.locator('input[placeholder*="字母"]').first().fill(createTestIdentifier('bdd_invalid_path'));
    const paths = page.locator('input[placeholder*="斜线"]');
    await paths.first().fill('https://example.com/not-a-path');
    await paths.last().fill('/get');
    await page.getByRole('button', { name: '提交', exact: true }).click();
    await expect(page.locator('.content-view .bk-form-error').filter({ hasText: /路径|斜线|URL/ }).first()).toBeVisible();
    await expect(page).toHaveURL(new RegExp('/resource/create$'));
  });
});
