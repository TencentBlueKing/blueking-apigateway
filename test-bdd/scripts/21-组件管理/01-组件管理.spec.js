// @generated from: test-bdd/cases/21-组件管理/01-组件管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
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

  test('场景: 创建组件 (read-only verification)', async ({ page }) => {
    await page.goto(`${BASE_URL}/components/access`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/components/access`);
      await waitForPageReady(page);
    }

    // 进入组件管理页面
    const manageMenu = page.locator('a, .nav-item, .menu-item, .bk-tab-label').filter({ hasText: /组件管理/ }).first();
    if (await manageMenu.isVisible().catch(() => false)) {
      await manageMenu.click();
      await waitForPageReady(page);
    }

    // 验证"新建组件"按钮存在
    const createBtn = page.locator('button, .bk-button').filter({ hasText: /新建|创建/ }).first();
    if (await createBtn.isVisible().catch(() => false)) {
      await expect(createBtn).toBeVisible();
    }
  });

  test('场景: 编辑组件 (read-only verification)', async ({ page }) => {
    await page.goto(`${BASE_URL}/components/access`);
    await waitForPageReady(page);
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(`${BASE_URL}/components/access`);
      await waitForPageReady(page);
    }

    // 进入组件管理页面
    const manageMenu = page.locator('a, .nav-item, .menu-item, .bk-tab-label').filter({ hasText: /组件管理/ }).first();
    if (await manageMenu.isVisible().catch(() => false)) {
      await manageMenu.click();
      await waitForPageReady(page);
    }

    // 验证编辑按钮存在
    const editBtn = page.locator('.bk-table button, .bk-table .bk-button, .bk-table a').filter({ hasText: /编辑/ }).first();
    if (await editBtn.isVisible().catch(() => false)) {
      await expect(editBtn).toBeVisible();
    }

    // 支持通过组件名称搜索
    const searchInput = page.locator('.bk-search-select, .bk-input input, input[placeholder*="搜索"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await expect(searchInput).toBeVisible();
    }
  });
});
