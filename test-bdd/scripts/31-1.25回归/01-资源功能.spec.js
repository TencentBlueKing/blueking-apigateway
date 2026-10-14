// @generated from: test-bdd/cases/31-1.25回归/01-资源功能.md
// @generated-date: 2026-10-14
const bodyExample = require('../../fixtures/1.25/request-body.json');
const { test, expect } = require('../../runtime/bdd-test');
const {
  BASE_URL, getGatewayId, pageApiGet, pageApiPut, pageApiDelete,
  unwrapApiData, createTestVersion, getActiveDialog, getActiveSideslider,
} = require('../../runtime/helpers');
const { createOwnedResource } = require('../../runtime/test-data');
const base = BASE_URL.replace(/\/$/, '');
const api = () => `/gateways/${getGatewayId()}/resources/`;
const detail = async (page, resource) => unwrapApiData(await pageApiGet(page, `${api()}${resource.id}/`));
const conflicts = async page => unwrapApiData(await pageApiGet(page, `${api()}-/path-conflicts/`));
const generationButton = page => page.getByRole('button', { name: /生成版本$/ }).filter({ hasNotText: '立即' });
async function edit(page, resource) {
  await page.goto(`${base}/${getGatewayId()}/resource/edit/${resource.id}`);
  await expect(page.locator('input[placeholder*="字母"]').first()).toHaveValue(resource.name);
  await page.getByText('请求参数', { exact: true }).click();
}
async function save(page, resource) {
  const saved = page.waitForResponse(r => r.url().endsWith(`/resources/${resource.id}/`) && r.request().method() === 'PUT');
  await page.getByRole('button', { name: '提交', exact: true }).click();
  const response = await saved;
  expect(response.status(), await response.text()).toBe(204);
  await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/resource/setting$`));
}

test.describe('功能: 1.25 资源功能回归', () => {
  const owned = [];
  test.beforeEach(async ({ page }) => { await page.goto(BASE_URL); });
  test.afterEach(async ({ page }) => {
    for (const resource of owned.splice(0)) await pageApiDelete(page, `${api()}${resource.id}/`);
  });
  async function resource(page) {
    const created = await createOwnedResource(page, getGatewayId());
    owned.push(created);
    return created;
  }

  test('场景: 等价参数路由按方法检测并在修改删除后更新', async ({ page }) => {
    const [a, b, post] = [await resource(page), await resource(page), await resource(page)];
    const prefix = `/bdd125/${a.name}`;
    const update = (r, suffix, method = 'GET') => pageApiPut(page, `${api()}${r.id}/`, {
      ...r.payload, method, path: `${prefix}/${suffix}/`,
    });
    await update(a, '{first}');
    await update(b, '{second}');
    await update(post, '{third}', 'POST');
    let detected = await conflicts(page);
    const group = detected.conflicts.find(g => g.resources.some(r => r.id === a.id));
    expect(group.method).toBe('GET');
    expect(group.resources.map(r => r.id).sort()).toEqual([a.id, b.id].sort());
    await page.goto(`${base}/${getGatewayId()}/resource/setting`);
    await expect(page.getByText(/检测到.*路由冲突/)).toBeVisible();
    await expect(page.getByText(a.name, { exact: true }).first()).toBeVisible();
    await update(b, 'other/{second}');
    detected = await conflicts(page);
    expect(detected.conflicts.some(g => g.resources.some(r => r.id === a.id || r.id === b.id))).toBe(false);
    await update(b, '{second}');
    expect((await conflicts(page)).conflicts.some(g => g.resources.some(r => r.id === a.id))).toBe(true);
    await pageApiDelete(page, `${api()}${a.id}/`);
    owned.splice(owned.indexOf(a), 1);
    expect((await conflicts(page)).conflicts.some(g => g.resources.some(r => r.id === b.id))).toBe(false);
  });

  test('场景: 未配置请求参数不会默认声明无参数', async ({ page }) => {
    const r = await resource(page);
    await edit(page, r);
    const checkbox = page.locator('label.bk-checkbox').filter({ hasText: '该资源无请求参数' });
    await expect(checkbox).not.toHaveClass(/is-checked/);
    await page.getByPlaceholder('请输入描述', { exact: true }).first().fill('BDD125 without schema');
    await save(page, r);
    await edit(page, r);
    await expect(checkbox).not.toHaveClass(/is-checked/);
  });

  test('场景: Header和Query参数保存后重开保留默认值与说明', async ({ page }) => {
    const r = await resource(page);
    await edit(page, r);
    const values = [
      ['header', 'Header', 'X-BDD125', 'header-default', 'header description'],
      ['query', 'Query', 'page', '5', 'page number'],
    ];
    for (const [, label, name, value, description] of values) {
      await page.getByText(`${label} (0)`, { exact: true }).click();
      await page.getByRole('button', { name: /新增参数/ }).filter({ visible: true }).click();
      await page.getByPlaceholder('参数名', { exact: true }).filter({ visible: true }).fill(name);
      await page.getByPlaceholder('默认值', { exact: true }).filter({ visible: true }).fill(value);
      await page.getByPlaceholder('说明', { exact: true }).filter({ visible: true }).fill(description);
    }
    await save(page, r);
    const parameters = (await detail(page, r)).schema.parameters;
    for (const [location, , name, value, description] of values) {
      expect(parameters).toContainEqual({ in: location, name, description, schema: { type: 'string', default: value } });
    }
    await edit(page, r);
    for (const [, label, name, value, description] of values) {
      await page.getByText(`${label} (1)`, { exact: true }).click();
      await expect(page.getByPlaceholder('参数名', { exact: true }).filter({ visible: true })).toHaveValue(name);
      await expect(page.getByPlaceholder('默认值', { exact: true }).filter({ visible: true })).toHaveValue(value);
      await expect(page.getByPlaceholder('说明', { exact: true }).filter({ visible: true })).toHaveValue(description);
    }
  });

  test('场景: JSON生成嵌套Body保存后重开保留结构', async ({ page }) => {
    const r = await resource(page);
    await pageApiPut(page, `${api()}${r.id}/`, { ...r.payload, method: 'POST' });
    await edit(page, r);
    await page.getByText('通过 JSON 生成', { exact: true }).filter({ visible: true }).click();
    const slider = getActiveSideslider(page);
    const editor = slider.locator('textarea');
    await editor.focus();
    await editor.press('ControlOrMeta+A');
    await editor.press('Backspace');
    await page.keyboard.insertText(JSON.stringify(bodyExample));
    await slider.getByRole('button', { name: '确定', exact: true }).click();
    await expect(slider).toBeHidden();
    await save(page, r);
    const schema = (await detail(page, r)).schema.requestBody.content['application/json'].schema;
    expect(schema.type).toBe('object');
    expect(schema.properties.profile.properties.name.type).toBe('string');
    expect(schema.properties.profile.properties.enabled.type).toBe('boolean');
    expect(schema.properties.items.type).toBe('array');
    expect(schema.properties.items.items.properties.id.type).toMatch(/integer|number/);
    expect(schema.properties.count.type).toMatch(/integer|number/);
    await edit(page, r);
    await page.getByText('Body (1)', { exact: true }).click();
    const names = page.getByPlaceholder('字段名', { exact: true }).filter({ visible: true });
    await expect(names.first()).toBeVisible();
    expect(await names.evaluateAll(es => es.map(e => e.value))).toEqual(expect.arrayContaining(['profile', 'items', 'count']));
  });

  test('场景: 批量编辑后无需刷新即可生成版本', async ({ page }, testInfo) => {
    const r = await resource(page);
    await createTestVersion(page, getGatewayId(), { createResource: false });
    const baseline = page.waitForResponse(res => res.url().endsWith('/resource-versions/need-new-version/'));
    await page.goto(`${base}/${getGatewayId()}/resource/setting`);
    expect((await (await baseline).json()).data.need_new_version).toBe(false);
    await expect(page.getByRole('row').filter({ hasText: r.name })).toBeVisible();
    await expect(generationButton(page)).toBeDisabled();
    await page.getByRole('button', { name: '批量操作', exact: true }).click();
    await page.getByRole('row').filter({ hasText: r.name }).locator('label.bk-checkbox').click();
    await page.getByRole('button', { name: '编辑资源', exact: true }).click();
    const dialog = getActiveDialog(page);
    await dialog.locator('label.bk-checkbox').filter({ hasText: '是否公开' }).click();
    const saved = page.waitForResponse(res => res.url().endsWith('/resources/batch/') && res.request().method() === 'PUT');
    await dialog.getByRole('button', { name: '确定', exact: true }).click();
    const response = await saved;
    expect(response.status(), await response.text()).toBe(204);
    await expect(dialog).toBeHidden();
    expect((await detail(page, r)).is_public).toBe(false);
    const need = unwrapApiData(await pageApiGet(page, `/gateways/${getGatewayId()}/resource-versions/need-new-version/`));
    expect(need.need_new_version).toBe(true);
    await testInfo.attach('batch-persisted-result', {
      body: JSON.stringify({ gateway: getGatewayId(), resource: r.id, request: response.request().postDataJSON(), need }),
      contentType: 'application/json',
    });
    await page.getByRole('button', { name: /退出批量编辑/ }).click();
    await expect(generationButton(page), '批量编辑已保存，生成版本应无需刷新即可启用').toBeEnabled();
  });

  test('场景: 省略可选WebSocket字段仍可更新资源认证', async ({ page }, testInfo) => {
    const r = await resource(page);
    const payload = {
      ...r.payload,
      auth_config: { ...r.payload.auth_config, resource_perm_required: true },
    };
    const response = await pageApiPut(page, `${api()}${r.id}/`, payload, { allowFailure: true });
    await testInfo.attach('resource-update-with-optional-field-omitted', {
      body: JSON.stringify({ resourceId: r.id, payload, response }), contentType: 'application/json',
    });
    expect(response.status, JSON.stringify(response.data)).toBe(204);
    expect((await detail(page, r)).auth_config.resource_perm_required).toBe(true);
  });
});
