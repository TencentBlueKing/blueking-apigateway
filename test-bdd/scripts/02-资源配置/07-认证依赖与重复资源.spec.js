// @generated from: test-bdd/cases/02-资源配置/07-认证依赖与重复资源.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, pageApiGet, pageApiPost, pageApiDelete, unwrapApiData, waitForBackendRequests } = require('../../runtime/helpers');
const { createOwnedResource } = require('../../runtime/test-data');

test.describe('功能: 资源配置 - 认证依赖与重复资源', () => {
  let resource;
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    resource = await createOwnedResource(page, getGatewayId());
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/edit/${resource.id}`);
    await expect(page.locator('input[placeholder*="字母"]').first()).toHaveValue(resource.name);
    await waitForBackendRequests(page);
  });
  test.afterEach(async ({ page }) => {
    if (resource) await pageApiDelete(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`);
    resource = undefined;
  });
  const authSwitch = (page, label) => page.locator('.auth-child-row').filter({ hasText: label }).locator('.bk-switcher');
  async function save(page) {
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().endsWith(`/resources/${resource.id}/`) && r.request().method() === 'PUT'),
      page.getByRole('button', { name: '提交', exact: true }).click(),
    ]);
    expect(response.ok(), await response.text()).toBe(true);
    return unwrapApiData(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`));
  }

  test('场景: 关闭用户认证清除个人令牌并持久化', async ({ page }) => {
    const token = authSwitch(page, '个人令牌');
    await token.click();
    await expect(token).toHaveClass(/is-checked/);
    await page.getByText('用户认证', { exact: true }).click();
    await expect(token).toHaveClass(/is-disabled/);
    await expect(token).toHaveClass(/is-unchecked/);
    const detail = await save(page);
    expect(detail.auth_config.auth_verified_required).toBe(false);
    expect(detail.auth_config.oauth2_personal_client_enabled).toBe(false);
  });

  test('场景: 关闭应用认证清除应用权限并禁止申请', async ({ page }) => {
    const permission = authSwitch(page, '检验应用权限');
    await permission.click();
    await expect(permission).toHaveClass(/is-checked/);
    await page.getByText('应用认证', { exact: true }).click();
    await expect(permission).toHaveClass(/is-disabled/);
    await expect(permission).toHaveClass(/is-unchecked/);
    await expect(authSwitch(page, '允许申请权限')).toHaveClass(/is-disabled/);
    const detail = await save(page);
    expect(detail.auth_config.app_verified_required).toBe(false);
    expect(detail.auth_config.resource_perm_required).toBe(false);
    expect(detail.allow_apply_permission).toBe(false);
  });

  test('场景: 重复名称和重复方法路径均拒绝且不覆盖原资源', async ({ page }) => {
    for (const overrides of [
      { path: `${resource.path}different/` },
      { name: `${resource.name}_duplicate` },
    ]) {
      const result = await pageApiPost(page, `/gateways/${getGatewayId()}/resources/`, {
        ...resource.payload, ...overrides,
      }, { allowFailure: true, retryHtml500: false });
      expect(result.status, JSON.stringify(result.data)).toBe(400);
      expect(result.data.error?.code).toBe('INVALID_ARGUMENT');
    }
    const detail = unwrapApiData(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`));
    expect(detail.name).toBe(resource.name);
    expect(detail.path).toBe(resource.path);
    expect(detail.description).toBe(resource.payload.description);
  });
});
