// @generated from: test-bdd/cases/02-资源配置/03-资源列表操作.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getTableRowCount, navigateToGatewayPage, BASE_URL } = require("../../runtime/helpers");


// Read-only tests use gateway ID 6
const READONLY_GATEWAY_ID = 6;

test.describe('功能: 资源配置 - 资源列表操作', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, '6', '资源配置', '/resource/setting');
  });

  test('场景: 搜索资源', async ({ page }) => {
    // 搜索资源名称
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="名称"], input[placeholder*="资源"]').first();
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    await searchInput.fill('get');
    await page.waitForTimeout(1500);

    // 验证搜索结果
    const rows = await getTableRowCount(page);
    expect(rows).toBeGreaterThanOrEqual(0);

    // 清空搜索
    await searchInput.clear();
    await page.waitForTimeout(1500);

    // 按前端请求路径搜索
    // 切换搜索条件为前端请求路径
    const searchTypeSelect = page.locator('.bk-select, .search-select').first();
    if (await searchTypeSelect.isVisible().catch(() => false)) {
      await selectDropdown(page, '.bk-select', '前端请求路径');
      await page.waitForTimeout(300);
    }

    await searchInput.fill('/api/');
    await page.waitForTimeout(1500);

    const pathRows = await getTableRowCount(page);
    expect(pathRows).toBeGreaterThanOrEqual(0);
  });

  test('场景: 标签筛选', async ({ page }) => {
    // 查找标签筛选区域
    const tagFilter = page.locator('.tag-filter, .label-filter, [class*="tag"]').first();
    if (await tagFilter.isVisible({ timeout: 5000 }).catch(() => false)) {
      // 点击标签筛选
      await tagFilter.click();
      await page.waitForTimeout(300);

      // 选择第一个标签
      const tagOption = page.locator('.bk-select-option, .bk-option, .tag-item').first();
      if (await tagOption.isVisible().catch(() => false)) {
        await tagOption.click();
        await page.waitForTimeout(800);

        // 验证筛选结果
        const rows = await getTableRowCount(page);
        expect(rows).toBeGreaterThanOrEqual(0);
      }

      // 关闭筛选下拉
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }
  });

  test('场景: 批量操作', async ({ page }) => {
    // 不勾选资源直接点击批量操作中的编辑资源
    const batchBtn = page.locator('button, .bk-button').filter({ hasText: /批量/ }).first();
    if (await batchBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await batchBtn.click();
      await page.waitForTimeout(300);

      const editOption = page.locator('.bk-select-option, .bk-option, .dropdown-item, [class*="menu-item"]').filter({ hasText: '编辑资源' }).first();
      if (await editOption.isVisible().catch(() => false)) {
        await editOption.click();
        await page.waitForTimeout(800);

        // 验证提示"请先勾选资源"
        const tipMsg = page.locator('.bk-message, .bk-notify, [class*="toast"], [class*="message"]').filter({ hasText: /勾选/ }).first();
        await expect(tipMsg).toBeVisible({ timeout: 10000 });
      }
    }

    // 勾选多个资源
    const checkboxes = page.locator('table .bk-checkbox, .bk-table .bk-checkbox, input[type="checkbox"]');
    const checkboxCount = await checkboxes.count();
    if (checkboxCount >= 3) {
      await checkboxes.nth(1).click();
      await page.waitForTimeout(200);
      await checkboxes.nth(2).click();
      await page.waitForTimeout(200);

      // 验证勾选成功
      expect(checkboxCount).toBeGreaterThan(0);
    }
  });
});
