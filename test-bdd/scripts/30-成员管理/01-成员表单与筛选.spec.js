// @generated from: test-bdd/cases/30-成员管理/01-成员表单与筛选.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId } = require('../../runtime/helpers');

test.describe('功能: 成员管理 - 表单与筛选', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL.replace(/\/$/, '')}/${getGatewayId()}/members`);
    await expect(page.getByRole('button', { name: '新增成员', exact: true })).toBeVisible();
    await expect(page.locator('.content-view table')).toContainText('admin');
  });

  test('场景: 新增成员必须选择用户', async ({ page }) => {
    await page.getByRole('button', { name: '新增成员', exact: true }).click();
    const form = page.locator('.bk-sideslider').filter({ hasText: '请输入人员名称搜索' });
    await form.getByRole('button', { name: '确定', exact: true }).click();
    await expect(page.locator('body')).toContainText('请选择人员');
    await expect(form.getByRole('button', { name: '确定', exact: true })).toBeVisible();
    await form.getByRole('button', { name: '取消', exact: true }).click();
    await expect(page.locator('.content-view table')).toContainText('admin');
  });

  test('场景: 查看角色权限并取消变更', async ({ page }) => {
    await page.getByRole('button', { name: '变更角色', exact: true }).click();
    const form = page.locator('.bk-sideslider').filter({ hasText: '变更角色' });
    await expect(form.getByRole('button', { name: '取消', exact: true })).toBeVisible();
    await expect(form).toContainText('管理员');
    await expect(form).toContainText('运营者');
    await expect(form).toContainText('成员管理');
    await form.getByRole('button', { name: '取消', exact: true }).click();
    await expect(page.locator('.content-view table')).toContainText('管理员');
  });

  test('场景: 搜索不存在的成员并恢复', async ({ page }) => {
    const search = page.getByPlaceholder('搜索用户名', { exact: true });
    await search.fill('bdd-no-such-user-1014');
    await search.press('Enter');
    await expect(page.locator('.content-view')).toContainText(/搜索结果为空|暂无数据/);
    await expect(page.locator('.content-view table')).not.toContainText('admin');
    await search.fill('');
    await search.press('Enter');
    await expect(page.locator('.content-view table')).toContainText('admin');
  });
});
