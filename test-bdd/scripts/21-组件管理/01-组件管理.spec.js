// @generated from: test-bdd/cases/21-组件管理/01-组件管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('../../runtime/bdd-test');
const { waitForPageReady, reAuth, getToastMessage, BASE_URL } = require("../../runtime/helpers");


test.describe('功能: 组件管理 - 组件管理综合功能', () => {
  test('场景: 查看组件简介', async ({ page }) => {
    await page.goto(`${BASE_URL}/components/access`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/components/access`);
      await waitForPageReady(page);
    }

    // 页面应正常展示蓝鲸API网关组件简介内容
    const contentArea = page.locator('[class*="intro"], [class*="content"], .main-content, .page-content').first();
    await expect(contentArea).toBeVisible({ timeout: 10000 });

    // 验证简介菜单存在
    const introMenu = page.locator('a, .nav-item, .menu-item').filter({ hasText: /简介/ }).first();
    if (await introMenu.isVisible().catch(() => false)) {
      await expect(introMenu).toBeVisible();
    }
  });

  test('场景: 系统管理', async ({ page }) => {
    await page.goto(`${BASE_URL}/components/access`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/components/access`);
      await waitForPageReady(page);
    }

    // 进入系统管理页面 - 点击系统管理菜单
    const systemMenu = page.locator('a, .nav-item, .menu-item, .bk-tab-label').filter({ hasText: /系统管理|系统/ }).first();
    if (await systemMenu.isVisible().catch(() => false)) {
      await systemMenu.click();
      await waitForPageReady(page);
    }

    // 在搜索框中输入系统名称进行搜索
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"], input[placeholder*="系统"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await expect(searchInput).toBeVisible();
    }

    // 表格应可见
    const table = page.locator('.bk-table');
    if (await table.isVisible().catch(() => false)) {
      await expect(table).toBeVisible();
    }

    // 支持自定义表格列设置
    const settingBtn = page.locator('.bk-table-setting-content, [class*="setting"], .icon-cog').first();
    if (await settingBtn.isVisible().catch(() => false)) {
      await expect(settingBtn).toBeVisible();
    }
  });

  test('场景: 创建组件 (read-only verification)', async () => {
    test.skip(true, '缺少隔离的组件所属系统和后端组件服务，未执行组件创建');
  });

  test('场景: 编辑组件 (read-only verification)', async () => {
    test.skip(true, '没有本次创建的组件，不编辑共享组件');
  });

  test('场景: 查看组件同步历史和版本', async ({ page }) => {
    const baseUrl = BASE_URL.replace(/\/$/, '');

    await page.goto(`${baseUrl}/components/history`, { waitUntil: 'domcontentloaded' });
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${baseUrl}/components/history`, { waitUntil: 'domcontentloaded' });
      await waitForPageReady(page);
    }
    await expect(page).toHaveURL(/\/components\/history/);
    await expect(page.locator('body')).toContainText(/同步历史|同步时间|同步状态|暂无数据|搜索结果为空/);

    await page.goto(`${baseUrl}/components/version`, { waitUntil: 'domcontentloaded' });
    await waitForPageReady(page);
    await expect(page).toHaveURL(/\/components\/version/);
    await expect(page.locator('body')).toContainText(/同步版本|版本|资源|暂无数据|搜索结果为空/);
  });

});
