// @generated from: test-bdd/cases/02-资源配置/04-资源插件.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const {
  clickConfirm,
  getActionButton,
  getActiveSideslider,
  getAvailablePluginSelectionOption,
  getPluginBindingItems,
  getPluginBindingItemByText,
  getToastMessage,
  navigateToGatewayPage,
  openFirstResourcePluginPanel,
  getGatewayId,
} = require("../../runtime/helpers");

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
    optionPattern: /限制请求大小|request body|body limit/i,
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
    optionPattern: /访问令牌|access token|token source/i,
    fillAdd: async (slider) => {
      await slider.locator('label, .bk-radio').filter({ hasText: /api_key/i }).first().click();
    },
    fillEdit: async (slider) => {
      await slider.locator('label, .bk-radio').filter({ hasText: /bearer/i }).first().click();

      const switcher = slider.locator('[role="switch"], .bk-switcher').first();
      if (await switcher.isVisible({ timeout: 2000 }).catch(() => false)) {
        await switcher.click();
      }
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
    optionPattern: /响应重写|response rewrite/i,
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
    optionPattern: /请求验证|request validation/i,
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
    optionPattern: /用户限制|user-restriction|bk-user-restriction/i,
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
    optionPattern: /IP限制|ip restriction|bk-ip-restriction/i,
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
    optionPattern: /限流|rate limit|bk-rate-limit/i,
    fillAdd: async (slider) => {
      const timesInput = slider.locator('.bk-form-item').filter({ hasText: /次数|times|tokens/i }).locator('input').first();
      const periodInput = slider.locator('.bk-form-item').filter({ hasText: /时间范围|period/i }).locator('input').first();
      await timesInput.fill('120');
      await periodInput.fill('2');
    },
    fillEdit: async (slider) => {
      const timesInput = slider.locator('.bk-form-item').filter({ hasText: /次数|times|tokens/i }).locator('input').first();
      const periodInput = slider.locator('.bk-form-item').filter({ hasText: /时间范围|period/i }).locator('input').first();
      await timesInput.fill('240');
      await periodInput.fill('4');
    },
  },
  {
    name: 'bk-header-rewrite',
    optionPattern: /请求头重写|header rewrite|bk-header-rewrite/i,
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

  const addPluginBtn = page.locator('button, .bk-button').filter({ hasText: /添加插件/ });
  await addPluginBtn.click();
  await page.waitForTimeout(800);

  const option = getAvailablePluginSelectionOption(page, pluginCase.optionPattern);
  await expect(option).toBeVisible({ timeout: 5000 });
  await option.click();
  await page.waitForTimeout(300);

  const addSlider = getActiveSideslider(page);
  const nextBtn = getActionButton(addSlider, '下一步');
  if (await nextBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await nextBtn.click();
    await page.waitForTimeout(800);
  }

  await pluginCase.fillAdd(addSlider);
  await expect(clickConfirm(page, /确定|确认/, addSlider)).resolves.toBe(true);
  await page.waitForTimeout(1500);

  const addedItem = getPluginBindingItemByText(page, pluginCase.optionPattern);
  await expect(bindingItems).toHaveCount(beforeCount + 1, { timeout: 10000 });
  await expect(addedItem).toBeVisible({ timeout: 10000 });

  const addToast = await getToastMessage(page);
  expect(addToast).toMatch(/成功|添加/);

  await addedItem.hover();
  await page.waitForTimeout(300);

  const editIcon = addedItem.locator('.icon-edit, [class*="edit"], .bk-icon').first();
  await expect(editIcon).toBeVisible({ timeout: 5000 });
  await editIcon.click();
  await page.waitForTimeout(800);

  const editSlider = getActiveSideslider(page);
  await pluginCase.fillEdit(editSlider);
  await expect(clickConfirm(page, /确定|确认/, editSlider)).resolves.toBe(true);
  await page.waitForTimeout(1500);

  const editToast = await getToastMessage(page);
  expect(editToast).toMatch(/成功|修改/);
  await expect(bindingItems).toHaveCount(beforeCount + 1, { timeout: 10000 });

  await addedItem.hover();
  await page.waitForTimeout(300);

  const deleteIcon = addedItem.locator('.icon-delete, [class*="delete"], .bk-icon').last();
  await expect(deleteIcon).toBeVisible({ timeout: 5000 });
  await deleteIcon.click();
  await page.waitForTimeout(800);

  await expect(clickConfirm(page, /确定|确认|停用/)).resolves.toBe(true);
  await page.waitForTimeout(1500);

  const deleteToast = await getToastMessage(page);
  expect(deleteToast).toMatch(/成功|停用/);
  await expect(bindingItems).toHaveCount(beforeCount, { timeout: 10000 });
}


test.describe('功能: 资源配置 - 资源插件', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 添加插件', async ({ page }) => {
    if (await openFirstResourcePluginPanel(page)) {

      const bindingItems = getPluginBindingItems(page);
      const beforeCount = await bindingItems.count();

      // 点击添加插件
      const addPluginBtn = page.locator('button, .bk-button').filter({ hasText: /添加插件/ });
      await addPluginBtn.click();
      await page.waitForTimeout(800);

      // 选择插件类型（优先 CORS，若已存在则选择第一个可用插件）
      const option = getAvailablePluginSelectionOption(page, CORS_PLUGIN_PATTERN);
      const fallbackOption = getAvailablePluginSelectionOption(page);
      if (await option.isVisible().catch(() => false)) {
        await option.click();
        await page.waitForTimeout(300);
      } else if (await fallbackOption.isVisible().catch(() => false)) {
        await fallbackOption.click();
        await page.waitForTimeout(300);
      }

      // 点击下一步
      const pluginSlider = getActiveSideslider(page);
      const nextBtn = getActionButton(pluginSlider, '下一步');
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(800);
      }

      // 填写配置信息（如 allow_origins）
      const configInput = pluginSlider.locator('textarea, input[placeholder*="origin"], .code-editor, .bk-textarea').first();
      if (await configInput.isVisible().catch(() => false)) {
        await configInput.fill('*');
      }

      // 点击确定
      if (await clickConfirm(page, /确定|确认/, pluginSlider)) {
        await page.waitForTimeout(2000);
        await expect(bindingItems).toHaveCount(beforeCount + 1, { timeout: 10000 });
      }
    }
  });

  test('场景: 编辑插件', async ({ page }) => {
    if (await openFirstResourcePluginPanel(page)) {

      const bindingItems = getPluginBindingItems(page);
      const beforeCount = await bindingItems.count();

      // 鼠标悬浮已有插件
      const pluginItem = bindingItems.first();
      if (await pluginItem.isVisible().catch(() => false)) {
        await pluginItem.hover();
        await page.waitForTimeout(300);

        // 点击编辑（铅笔图标）
        const editIcon = pluginItem.locator('.icon-edit, [class*="edit"], .bk-icon').first();
        if (await editIcon.isVisible().catch(() => false)) {
          await editIcon.click();
          await page.waitForTimeout(800);

          const pluginSlider = getActiveSideslider(page);

          // 修改配置信息
          const configInput = pluginSlider.locator('textarea, .code-editor, .bk-textarea').first();
          if (await configInput.isVisible().catch(() => false)) {
            await configInput.clear();
            await configInput.fill('http://example.com');
          }

          // 点击确定
          const confirmed = await clickConfirm(page, /确定|确认/, pluginSlider);
          if (confirmed) {
            await page.waitForTimeout(2000);
          }

          // 验证修改成功
          const toast = await getToastMessage(page);
          expect(toast).toMatch(/成功|修改/);
          await expect(bindingItems).toHaveCount(beforeCount, { timeout: 10000 });
        }
      }
    }
  });

  test('场景: 删除插件', async ({ page }) => {
    if (await openFirstResourcePluginPanel(page)) {

      const bindingItems = getPluginBindingItems(page);
      const beforeCount = await bindingItems.count();

      // 鼠标悬浮已有插件
      const pluginItem = bindingItems.first();
      if (await pluginItem.isVisible().catch(() => false)) {
        await pluginItem.hover();
        await page.waitForTimeout(300);

        // 点击删除（垃圾桶图标）
        const deleteIcon = pluginItem.locator('.icon-delete, [class*="delete"], .bk-icon').last();
        if (await deleteIcon.isVisible().catch(() => false)) {
          await deleteIcon.click();
          await page.waitForTimeout(800);

          // 确认停用
          if (await clickConfirm(page, /确定|确认|停用/)) {
            await page.waitForTimeout(2000);

            // 验证停用成功
            const toast = await getToastMessage(page);
            expect(toast).toMatch(/成功|停用/);
            await expect(bindingItems).toHaveCount(Math.max(0, beforeCount - 1), { timeout: 10000 });
          }
        }
      }
    }
  });

  test('场景: 通用插件矩阵', async ({ page }) => {
    if (await openFirstResourcePluginPanel(page)) {
      for (const pluginCase of GENERIC_PLUGIN_CASES) {
        await test.step(`通用插件 CRUD: ${pluginCase.name}`, async () => {
          await runGenericPluginCrudCycle(page, pluginCase);
        });
      }
    }
  });
});
