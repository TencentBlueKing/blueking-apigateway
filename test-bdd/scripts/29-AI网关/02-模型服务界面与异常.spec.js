// @generated from: test-bdd/cases/29-AI网关/02-模型服务界面与异常.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, pageApiGet, pageApiPost, unwrapApiResults } = require('../../runtime/helpers');
const { createOwnedGateway, deleteOwnedGateway } = require('../../runtime/test-data');

test.describe('功能: AI网关 - 模型服务界面与异常', () => {
  let gateway;
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    gateway = await createOwnedGateway(page, 2);
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${gateway.id}/model-services`);
    await expect(page.getByPlaceholder('请输入模型服务名称')).toBeVisible();
  });
  test.afterEach(async ({ page }) => {
    if (gateway) await deleteOwnedGateway(page, gateway);
    gateway = undefined;
  });

  async function openForm(page) {
    await page.getByRole('button', { name: '新建', exact: true }).click();
    const form = page.locator('.model-service-slider');
    await expect(form.getByRole('button', { name: '保存', exact: true })).toBeVisible();
    return form;
  }

  test('场景: 模型服务深链接和空列表', async ({ page }) => {
    await expect(page.locator('.model-service-content')).toContainText('暂无数据');
    await page.reload();
    await expect(page.getByPlaceholder('请输入模型服务名称')).toBeVisible();
    await expect(page.locator('.model-service-content')).toContainText('暂无数据');
  });

  test('场景: 未完成配置和未连接时禁止保存', async ({ page }) => {
    const form = await openForm(page);
    await expect(form.getByRole('button', { name: '保存', exact: true })).toBeDisabled();
    await form.getByPlaceholder('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头').fill('bdd-model');
    await form.getByPlaceholder('格式如：api.example.com/v1/chat/completions').fill('example.com/v1/chat/completions');
    await expect(form.getByRole('button', { name: '保存', exact: true })).toBeDisabled();
    await expect(form).toContainText('未测试');
    await form.getByPlaceholder('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头').fill('invalid_name');
    await form.getByPlaceholder('请输入描述').click();
    await expect(form.locator('.bk-form-error').first()).toBeVisible();
  });

  test('场景: 连通测试失败展示原因并禁止保存', async ({ page }) => {
    const form = await openForm(page);
    await form.getByPlaceholder('请输入 1-20 字符的字母、数字、连字符(-)，以字母开头').fill('bdd-model');
    await form.getByPlaceholder('格式如：api.example.com/v1/chat/completions').fill('bdd-unreachable.invalid/v1/chat/completions');
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('/backends/test-connection/') && r.request().method() === 'POST'),
      form.getByRole('button', { name: '连通测试', exact: true }).click(),
    ]);
    expect(response.status(), await response.text()).toBe(400);
    await expect(form).toContainText('连通失败');
    await expect(form).toContainText(/无法解析|不安全|连接失败/);
    await expect(form.getByRole('button', { name: '保存', exact: true })).toBeDisabled();
    const backends = unwrapApiResults(await pageApiGet(page, `/gateways/${gateway.id}/backends/`));
    expect(backends.some(row => row.name === 'bdd-model')).toBe(false);
  });

  test('场景: 超时和Provider异常返回明确校验错误', async ({ page }) => {
    const stages = unwrapApiResults(await pageApiGet(page, `/gateways/${gateway.id}/stages/`));
    expect(stages.length).toBeGreaterThan(0);
    for (const config of [
      { provider: 'not-a-provider', endpoint: 'https://example.com/v1/chat/completions', timeout: 30 },
      { provider: 'openai-compatible', endpoint: 'https://example.com/v1/chat/completions', timeout: 0 },
      { provider: 'openai-compatible', endpoint: 'https://example.com/v1/chat/completions', timeout: 301 },
    ]) {
      const result = await pageApiPost(page, `/gateways/${gateway.id}/backends/`, {
        name: 'bdd-invalid', type: 'http', kind: 'ai', configs: [{ stage_id: stages[0].id, ...config }],
      }, { allowFailure: true, retryHtml500: false });
      expect(result.status, JSON.stringify(result.data)).toBe(400);
      expect(result.data.error?.code).toBe('INVALID_ARGUMENT');
      expect(result.data.error?.message).toMatch(/provider|timeout|超时/i);
    }
  });
});
