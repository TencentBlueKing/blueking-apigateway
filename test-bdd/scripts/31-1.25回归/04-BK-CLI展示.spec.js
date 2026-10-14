// @generated from: test-bdd/cases/31-1.25回归/04-BK-CLI展示.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, pageApiGet, unwrapApiData } = require('../../runtime/helpers');

test.describe('功能: 1.25 BK-CLI 展示', () => {
  test('场景: 切换功能概览快速开始与进阶用法', async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/bk-cli`);
    await expect(page.getByRole('columnheader', { name: '能力描述', exact: true })).toBeVisible();
    await page.getByText('快速开始', { exact: true }).click();
    const quick = page.locator('.quick-start:visible');
    await expect(quick).toContainText('安装 CLI');
    await expect(quick).toContainText('认证配置');
    const environment = unwrapApiData(await pageApiGet(page, '/settings/env-vars/'));
    expect(environment.CLI.BK_API_URL_TMPL).toBeTruthy();
    await expect(quick).toContainText(environment.CLI.BK_API_URL_TMPL);
    await page.getByText('进阶用法', { exact: true }).first().click();
    const advanced = page.locator('.advanced-usage:visible');
    await expect(advanced).toContainText('多上下文管理');
    await expect(advanced).toContainText('--dry-run');
    await page.getByText('功能概览', { exact: true }).click();
    await expect(page.getByRole('columnheader', { name: '能力描述', exact: true })).toBeVisible();
  });
});
