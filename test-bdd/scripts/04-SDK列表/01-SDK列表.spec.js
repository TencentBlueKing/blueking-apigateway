// @generated from: test-bdd/cases/04-SDK列表/01-SDK列表.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, waitForBackendRequests } = require('../../runtime/helpers');

test.describe('功能: SDK列表 - SDK列表', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/resource/version`);
    await page.getByText('SDK 列表', { exact: true }).click();
    await expect(page.getByPlaceholder('请输入 SDK 版本号，资源版本或语言')).toBeVisible();
    await waitForBackendRequests(page);
  });
  test('场景: 查看SDK列表', async ({ page }) => {
    await expect(page.locator('.content-view table')).toBeVisible();
    await expect(page.locator('.content-view')).toContainText('SDK 名称');
    await page.getByRole('button', { name: '生成 SDK', exact: true }).click();
    const dialog = page.locator('.dialog-scroll-y');
    await expect(dialog.getByPlaceholder('请输入 SDK 版本号')).toBeVisible();
    await dialog.getByRole('button', { name: '确定', exact: true }).click();
    await expect(dialog.locator('.bk-form-error').first()).toContainText('必填项');
    await dialog.getByRole('button', { name: '取消', exact: true }).click();
  });
  test('场景: SDK筛选', async ({ page }) => {
    const keyword = `bdd-no-such-sdk-${Date.now()}`;
    const [response] = await Promise.all([
      page.waitForResponse(r => new URL(r.url()).pathname.endsWith(`/gateways/${getGatewayId()}/sdks/`)
        && new URL(r.url()).searchParams.get('keyword') === keyword),
      (async () => {
        const input = page.getByPlaceholder('请输入 SDK 版本号，资源版本或语言');
        await input.fill(keyword);
        await input.blur();
      })(),
    ]);
    expect(response.status()).toBe(200);
    expect((await response.json()).data.results).toEqual([]);
    await expect(page.locator('.content-view')).toContainText(/搜索结果为空|暂无数据/);
  });
  test('场景: SDK生成与下载', async () => {
    test.skip(true, '生成操作会上传到PyPI或制品库；本次未配置可回收的SDK测试仓库，未验证生成和下载');
  });
});
