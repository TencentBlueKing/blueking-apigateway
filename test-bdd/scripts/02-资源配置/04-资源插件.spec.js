// @generated from: test-bdd/cases/02-资源配置/04-资源插件.md
// @generated-date: 2026-03-31

const { test, expect } = require('../../runtime/bdd-test');
const {
  clickConfirm,
  pageApiGet,
  unwrapApiData,
  getActionButton,
  getActiveSideslider,
  getAvailablePluginSelectionOption,
  getPluginBindingItems,
  getPluginBindingItemByText,
  navigateToGatewayPage,
  pageApiDelete,
  getTableRowByText,
  getGatewayId,
} = require("../../runtime/helpers");

const { createOwnedResource } = require('../../runtime/test-data');

const CORS_PLUGIN_PATTERN = /CORS|跨域/;
const GENERIC_PLUGIN_CASES = [
  {
    name: 'redirect',
    optionPattern: /重定向|redirect/i,
    fillAdd: async (slider) => {
      const uriInput = slider.locator('.bk-form-item').filter({ hasText: /重定向 URI|uri/i }).locator('input').first();
      const codeInput = slider.locator('.bk-form-item').filter({ hasText: /HTTP 响应码|ret_code/i }).locator('input').first();
      await uriInput.fill('/matrix-redirect-add');
      await codeInput.fill('302');
    },
    fillEdit: async (slider) => {
      const uriInput = slider.locator('.bk-form-item').filter({ hasText: /重定向 URI|uri/i }).locator('input').first();
      const codeInput = slider.locator('.bk-form-item').filter({ hasText: /HTTP 响应码|ret_code/i }).locator('input').first();
      await uriInput.fill('/matrix-redirect-edit');
      await codeInput.fill('307');
    },
  },
  {
    name: 'request-body-limit',
    optionPattern: /限制请求体?大小|request body|body limit/i,
    fillAdd: async (slider) => {
      const bodySizeInput = slider.locator('.bk-form-item').filter({ hasText: /max_body_size|最大请求体大小/i }).locator('input').first();
      await bodySizeInput.fill('1024');
    },
    fillEdit: async (slider) => {
      const bodySizeInput = slider.locator('.bk-form-item').filter({ hasText: /max_body_size|最大请求体大小/i }).locator('input').first();
      await bodySizeInput.fill('2048');
    },
  },
  {
    name: 'proxy-cache',
    optionPattern: /代理缓存|proxy.?cache/i,
    fillAdd: async (slider) => {
      const ttlInput = slider.locator('.bk-form-item').filter({ hasText: /cache_ttl/i }).locator('input').first();
      await ttlInput.fill('300');
    },
    fillEdit: async (slider) => {
      const ttlInput = slider.locator('.bk-form-item').filter({ hasText: /cache_ttl/i }).locator('input').first();
      await ttlInput.fill('600');
    },
  },
  {
    name: 'access-token-source',
    optionPattern: /访问令牌|access.?token.*来源|token source/i,
    fillAdd: async (slider) => {
      await slider.locator('label, .bk-radio').filter({ hasText: /api_key/i }).first().click();
    },
    fillEdit: async (slider) => {
      await slider.locator('label, .bk-radio').filter({ hasText: /bearer/i }).first().click();

      const switcher = slider.locator('[role="switch"], .bk-switcher').first();
      await expect(switcher).toBeVisible();
      await switcher.click();
    },
  },
  {
    name: 'bk-mock',
    optionPattern: /mock|模拟/i,
    fillAdd: async (slider) => {
      const statusInput = slider.locator('.bk-form-item').filter({ hasText: /响应状态码|response_status/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /响应体|response_example/i }).locator('textarea').first();
      await statusInput.fill('201');
      await bodyInput.fill('{"message":"mock-add"}');
    },
    fillEdit: async (slider) => {
      const statusInput = slider.locator('.bk-form-item').filter({ hasText: /响应状态码|response_status/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /响应体|response_example/i }).locator('textarea').first();
      await statusInput.fill('202');
      await bodyInput.fill('{"message":"mock-edit"}');
    },
  },
  {
    name: 'fault-injection',
    optionPattern: /故障注入|fault/i,
    fillAdd: async (slider) => {
      const statusInput = slider.locator('.bk-form-item').filter({ hasText: /中断状态码|http_status/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /中断响应体|abort\.body/i }).locator('textarea').first();
      const percentageInput = slider.locator('.bk-form-item').filter({ hasText: /中断请求占比|percentage/i }).locator('input').first();
      await statusInput.fill('418');
      await bodyInput.fill('fault-add');
      await percentageInput.fill('80');
    },
    fillEdit: async (slider) => {
      const statusInput = slider.locator('.bk-form-item').filter({ hasText: /中断状态码|http_status/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /中断响应体|abort\.body/i }).locator('textarea').first();
      const percentageInput = slider.locator('.bk-form-item').filter({ hasText: /中断请求占比|percentage/i }).locator('input').first();
      await statusInput.fill('429');
      await bodyInput.fill('fault-edit');
      await percentageInput.fill('60');
    },
  },
  {
    name: 'response-rewrite',
    optionPattern: /响应重写|response.*转换|response rewrite/i,
    fillAdd: async (slider) => {
      const statusInput = slider.locator('.bk-form-item').filter({ hasText: /状态码|status_code/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /响应体|body/i }).locator('textarea').first();
      await statusInput.fill('204');
      await bodyInput.fill('rewrite-add');
    },
    fillEdit: async (slider) => {
      const statusInput = slider.locator('.bk-form-item').filter({ hasText: /状态码|status_code/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /响应体|body/i }).locator('textarea').first();
      await statusInput.fill('206');
      await bodyInput.fill('rewrite-edit');
    },
  },
  {
    name: 'api-breaker',
    optionPattern: /熔断|api breaker/i,
    fillAdd: async (slider) => {
      const codeInput = slider.locator('.bk-form-item').filter({ hasText: /熔断响应状态码|break_response_code/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /熔断响应体|break_response_body/i }).locator('textarea').first();
      const secInput = slider.locator('.bk-form-item').filter({ hasText: /最大熔断时间|max_breaker_sec/i }).locator('input').first();
      await codeInput.fill('503');
      await bodyInput.fill('breaker-add');
      await secInput.fill('180');
    },
    fillEdit: async (slider) => {
      const codeInput = slider.locator('.bk-form-item').filter({ hasText: /熔断响应状态码|break_response_code/i }).locator('input').first();
      const bodyInput = slider.locator('.bk-form-item').filter({ hasText: /熔断响应体|break_response_body/i }).locator('textarea').first();
      const secInput = slider.locator('.bk-form-item').filter({ hasText: /最大熔断时间|max_breaker_sec/i }).locator('input').first();
      await codeInput.fill('504');
      await bodyInput.fill('breaker-edit');
      await secInput.fill('120');
    },
  },
  {
    name: 'request-validation',
    optionPattern: /请求校验|request validation/i,
    fillAdd: async (slider) => {
      const bodySchemaInput = slider.locator('.bk-form-item').filter({ hasText: /请求体 JSON Schema|body_schema/i }).locator('textarea').first();
      const headerSchemaInput = slider.locator('.bk-form-item').filter({ hasText: /请求头 JSON Schema|header_schema/i }).locator('textarea').first();
      const rejectedCodeInput = slider.locator('.bk-form-item').filter({ hasText: /拒绝状态码|rejected_code/i }).locator('input').first();
      const rejectedMsgInput = slider.locator('.bk-form-item').filter({ hasText: /拒绝信息|rejected_msg/i }).locator('textarea').last();
      await bodySchemaInput.fill('{"type":"object","properties":{"name":{"type":"string"}}}');
      await headerSchemaInput.fill('{"type":"object","properties":{"x-request-id":{"type":"string"}}}');
      await rejectedCodeInput.fill('401');
      await rejectedMsgInput.fill('validation-add');
    },
    fillEdit: async (slider) => {
      const bodySchemaInput = slider.locator('.bk-form-item').filter({ hasText: /请求体 JSON Schema|body_schema/i }).locator('textarea').first();
      const headerSchemaInput = slider.locator('.bk-form-item').filter({ hasText: /请求头 JSON Schema|header_schema/i }).locator('textarea').first();
      const rejectedCodeInput = slider.locator('.bk-form-item').filter({ hasText: /拒绝状态码|rejected_code/i }).locator('input').first();
      const rejectedMsgInput = slider.locator('.bk-form-item').filter({ hasText: /拒绝信息|rejected_msg/i }).locator('textarea').last();
      await bodySchemaInput.fill('{"type":"object","properties":{"id":{"type":"integer"}}}');
      await headerSchemaInput.fill('{"type":"object","properties":{"x-bk-app-code":{"type":"string"}}}');
      await rejectedCodeInput.fill('422');
      await rejectedMsgInput.fill('validation-edit');
    },
  },
  {
    name: 'bk-user-restriction',
    optionPattern: /用户访问限制|用户限制|user-restriction|bk-user-restriction/i,
    fillAdd: async (slider) => {
      const whitelistItem = slider.locator('.bk-form-item').filter({ hasText: /白名单|whitelist/i }).last();
      const addUserIcon = whitelistItem.locator('.icon-ag-plus-circle-shape, [name="plus-circle-shape"]').first();
      const messageInput = slider.locator('.bk-form-item').filter({ hasText: /message/i }).locator('input').first();
      await addUserIcon.click();
      await whitelistItem.locator('.bk-input input, input').first().fill('matrix-user-add');
      await messageInput.fill('user restriction add');
    },
    fillEdit: async (slider) => {
      const whitelistItem = slider.locator('.bk-form-item').filter({ hasText: /白名单|whitelist/i }).last();
      const messageInput = slider.locator('.bk-form-item').filter({ hasText: /message/i }).locator('input').first();
      await whitelistItem.locator('.bk-input input, input').first().fill('matrix-user-edit');
      await messageInput.fill('user restriction edit');
    },
  },
  {
    name: 'bk-ip-restriction',
    optionPattern: /IP.*访问保护|IP限制|ip restriction|bk-ip-restriction/i,
    fillAdd: async (slider) => {
      const whitelistItem = slider.locator('.bk-form-item').filter({ hasText: /白名单|whitelist/i }).last();
      const whitelistInput = whitelistItem.locator('textarea, .bk-textarea textarea').first();
      await whitelistInput.fill('# matrix add\n192.168.1.10\n192.168.1.11');
    },
    fillEdit: async (slider) => {
      const whitelistItem = slider.locator('.bk-form-item').filter({ hasText: /白名单|whitelist/i }).last();
      const whitelistInput = whitelistItem.locator('textarea, .bk-textarea textarea').first();
      await whitelistInput.fill('# matrix edit\n10.10.10.10');
    },
  },
  {
    name: 'bk-rate-limit',
    optionPattern: /频率控制|限流|rate limit|bk-rate-limit/i,
    fillAdd: async (slider) => {
      const timesInput = slider.locator('.bk-form-item').filter({ hasText: /次数|times|tokens/i }).locator('input').first();
      await timesInput.fill('120');
    },
    fillEdit: async (slider) => {
      const timesInput = slider.locator('.bk-form-item').filter({ hasText: /次数|times|tokens/i }).locator('input').first();
      await timesInput.fill('240');
    },
  },
  {
    name: 'bk-header-rewrite',
    optionPattern: /header.*转换|请求头重写|header rewrite|bk-header-rewrite/i,
    fillAdd: async (slider) => {
      const setSection = slider.locator('.form-set').first();
      await setSection.locator('.icon-ag-plus-circle-shape').click();
      const rowInputs = setSection.locator('.custom-plugin-form-item input');
      await rowInputs.nth(0).fill('X-Matrix-Add');
      await rowInputs.nth(1).fill('matrix-add');
    },
    fillEdit: async (slider) => {
      const setSection = slider.locator('.form-set').first();
      const rowInputs = setSection.locator('.custom-plugin-form-item input');
      await rowInputs.nth(0).fill('X-Matrix-Edit');
      await rowInputs.nth(1).fill('matrix-edit');
    },
  },
];

async function runGenericPluginCrudCycle(page, pluginCase) {
  const bindingItems = getPluginBindingItems(page);
  const beforeCount = await bindingItems.count();

  const addPluginBtn = page.locator('button').filter({ hasText: /添加插件|立即添加/ }).first();
  await addPluginBtn.click();
  await page.waitForTimeout(800);

  const option = getAvailablePluginSelectionOption(page, pluginCase.optionPattern);
  await expect(option).toBeVisible({ timeout: 5000 });
  await option.click();
  await page.waitForTimeout(300);

  const addSlider = getActiveSideslider(page);
  const nextBtn = getActionButton(addSlider, '下一步');
  await nextBtn.click();

  await pluginCase.fillAdd(addSlider);
  const [created] = await Promise.all([
    page.waitForResponse(r => r.url().includes('/plugins/resource/') && r.request().method() === 'POST'),
    clickConfirm(page, /确定|确认/, addSlider).then(clicked => expect(clicked).toBe(true)),
  ]);
  expect(created.status(), await created.text()).toBe(201);
  const id = (await created.json()).data.id;
  const detailUrl = `${created.url()}${id}/`;
  const original = unwrapApiData(await pageApiGet(page, detailUrl));
  expect(original.yaml).toBeTruthy();

  const addedItem = getPluginBindingItemByText(page, pluginCase.optionPattern);
  await expect(bindingItems).toHaveCount(beforeCount + 1, { timeout: 10000 });
  await expect(addedItem).toBeVisible({ timeout: 10000 });


  await addedItem.hover();
  await page.waitForTimeout(300);

  const editIcon = addedItem.locator('.icon-edit, [class*="edit"], .bk-icon').first();
  await expect(editIcon).toBeVisible({ timeout: 5000 });
  await editIcon.click();
  await page.waitForTimeout(800);

  const editSlider = getActiveSideslider(page);
  await pluginCase.fillEdit(editSlider);
  const [updated] = await Promise.all([
    page.waitForResponse(r => r.url() === detailUrl && r.request().method() === 'PUT'),
    clickConfirm(page, /确定|确认/, editSlider).then(clicked => expect(clicked).toBe(true)),
  ]);
  expect(updated.ok(), await updated.text()).toBe(true);
  const changed = unwrapApiData(await pageApiGet(page, detailUrl));
  expect(changed.yaml).not.toBe(original.yaml);
  await expect(bindingItems).toHaveCount(beforeCount + 1, { timeout: 10000 });

  await addedItem.hover();
  await page.waitForTimeout(300);

  const deleteIcon = addedItem.locator('.icon-ag-delet, .icon-delete, [class*="delete"], .bk-icon').last();
  await expect(deleteIcon).toBeVisible({ timeout: 5000 });
  await deleteIcon.click();
  await page.waitForTimeout(800);

  const [deleted] = await Promise.all([
    page.waitForResponse(r => r.url() === detailUrl && r.request().method() === 'DELETE'),
    clickConfirm(page, /确定|确认|停用/).then(clicked => expect(clicked).toBe(true)),
  ]);
  expect(deleted.status(), await deleted.text()).toBe(204);
  await expect(bindingItems).toHaveCount(beforeCount, { timeout: 10000 });
}


async function fillCors(slider, origin) {
  for (const [key, value] of [
    ['allow_origins', origin], ['allow_methods', 'GET'],
    ['allow_headers', 'X-BDD'], ['expose_headers', 'X-BDD'],
  ]) await slider.locator(`.form-${key} input`).first().fill(value);
}

async function addCors(page) {
    await page.locator('button').filter({ hasText: /添加插件|立即添加/ }).first().click();
    const option = getAvailablePluginSelectionOption(page, CORS_PLUGIN_PATTERN);
    await expect(option).toBeVisible();
    await option.click();
    const form = getActiveSideslider(page);
    await form.getByRole('button', { name: '下一步', exact: true }).click();
    await fillCors(form, 'https://bdd-add.example.com');
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/bk-cors/configs/') && r.request().method() === 'POST'),
      form.getByRole('button', { name: '确定', exact: true }).click(),
    ]);
    expect(response.status(), await response.text()).toBe(201);
    const id = (await response.json()).data.id;
    const detail = unwrapApiData(await pageApiGet(page, `${response.url()}${id}/`));
    expect(detail.yaml).toContain('https://bdd-add.example.com');
    await expect(getPluginBindingItemByText(page, CORS_PLUGIN_PATTERN)).toBeVisible();
}

test.describe('功能: 资源配置 - 资源插件', () => {
  let resource;
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
    resource = await createOwnedResource(page, getGatewayId());
    await page.reload();
    const row = getTableRowByText(page, resource.name);
    await row.getByRole('button').filter({ hasText: /^\s*0(?:\s|$)/ }).click();
    await expect(page.locator('button').filter({ hasText: /添加插件|立即添加/ }).first()).toBeVisible();
  });
  test.afterEach(async ({ page }) => {
    if (resource) await pageApiDelete(page, `/gateways/${getGatewayId()}/resources/${resource.id}/`);
    resource = undefined;
  });

  test('场景: 添加插件', async ({ page }) => {
    await addCors(page);
  });

  test('场景: 编辑插件', async ({ page }) => {
    await addCors(page);
    const item = getPluginBindingItemByText(page, CORS_PLUGIN_PATTERN);
    await expect(item).toBeVisible();
    await item.hover();
    await item.locator('.icon-ag-edit-line').click();
    const form = getActiveSideslider(page);
    await fillCors(form, 'https://bdd-edit.example.com');
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/bk-cors/configs/') && r.request().method() === 'PUT'),
      form.getByRole('button', { name: '确定', exact: true }).click(),
    ]);
    expect(response.ok(), await response.text()).toBe(true);
    const detail = unwrapApiData(await pageApiGet(page, response.url()));
    expect(detail.yaml).toContain('https://bdd-edit.example.com');
  });

  test('场景: 删除插件', async ({ page }) => {
    await addCors(page);
    const item = getPluginBindingItemByText(page, CORS_PLUGIN_PATTERN);
    await expect(item).toBeVisible();
    await item.hover();
    await item.locator('.icon-ag-delet').click();
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/bk-cors/configs/') && r.request().method() === 'DELETE'),
      clickConfirm(page, /确定|确认|停用/).then(clicked => expect(clicked).toBe(true)),
    ]);
    expect(response.status(), await response.text()).toBe(204);
    await expect(getPluginBindingItemByText(page, CORS_PLUGIN_PATTERN)).toHaveCount(0);
  });

  for (const pluginCase of GENERIC_PLUGIN_CASES) {
    test(`场景: 通用插件增改删 - ${pluginCase.name}`, async ({ page }) => {
      await runGenericPluginCrudCycle(page, pluginCase);
    });
  }
});
