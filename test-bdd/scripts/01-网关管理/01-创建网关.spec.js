// @generated from: test-bdd/cases/01-网关管理/01-创建网关.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, createTestName, pageApiGet, unwrapApiData } = require('../../runtime/helpers');
const { deleteOwnedGateway } = require('../../runtime/test-data');

test.describe('功能: 网关管理 - 创建网关', () => {
  let ownedGateway;
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/create-gateway`);
    await expect(page.getByRole('button', { name: '确定', exact: true })).toBeVisible();
    await expect(page.getByText('admin (管理员)', { exact: true })).toBeVisible();
  });
  test.afterEach(async ({ page }) => {
    if (ownedGateway) await deleteOwnedGateway(page, ownedGateway);
    ownedGateway = undefined;
  });

  async function createGateway(page, isPublic, ai = false) {
    const suffix = createTestName('bdd-ui');
    if (ai) await page.getByText('AI 网关', { exact: true }).click();
    await page.locator('input[placeholder*="小写字母"]').fill(suffix);
    const toggle = page.locator('.bk-switcher');
    await expect(toggle).toBeVisible();
    const checked = await toggle.getAttribute('class');
    if (Boolean(checked.includes('is-checked')) !== isPublic) await toggle.click();
    const pending = page.waitForResponse(r => r.url().endsWith('/backend/gateways/') && r.request().method() === 'POST');
    await page.getByRole('button', { name: '确定', exact: true }).click();
    const response = await pending;
    expect(response.status(), await response.text()).toBe(201);
    const id = (await response.json()).data.id;
    ownedGateway = { id, name: ai ? `bkai-${suffix}` : suffix };
    const detail = unwrapApiData(await pageApiGet(page, `/gateways/${id}/`));
    expect(detail.name).toBe(ownedGateway.name);
    expect(detail.is_public).toBe(isPublic);
    expect(Number(detail.kind)).toBe(ai ? 2 : 0);
    return detail;
  }

  test('场景: 创建普通网关', async ({ page }) => { await createGateway(page, true); });
  test('场景: 创建私有网关', async ({ page }) => { await createGateway(page, false); });
  test('场景: 创建AI网关并自动添加前缀', async ({ page }) => { await createGateway(page, false, true); });
  test('场景: 创建可编程网关', async () => {
    test.skip(true, '需要可用代码仓库、开发语言及仓库访问凭证；不能用 example.com 声称发布成功');
  });
  test('场景: 名称校验', async ({ page }) => {
    await page.getByRole('button', { name: '确定', exact: true }).click();
    await expect(page.locator('.bk-form-error').filter({ hasText: '请填写名称' })).toBeVisible();
    await page.locator('input[placeholder*="小写字母"]').fill('1234invalid');
    await page.getByRole('button', { name: '确定', exact: true }).click();
    await expect(page.locator('.bk-form-error').filter({ hasText: /小写字母/ })).toBeVisible();
    await expect(page).toHaveURL(/\/create-gateway$/);
  });
});
