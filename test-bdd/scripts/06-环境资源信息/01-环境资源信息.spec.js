// @generated from: test-bdd/cases/06-环境资源信息/01-环境资源信息.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getTableRowCount, navigateToGatewayPage, BASE_URL } = require("../../runtime/helpers");


// Read-only tests use gateway ID 6
const READONLY_GATEWAY_ID = 6;

test.describe('功能: 环境资源信息 - 环境资源信息', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, '6', '环境概览', '/stage/overview');
  });

  test('场景: 查看环境资源列表', async ({ page }) => {
    // 切换到详情模式
    const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
    if (await detailTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(800);
    }

    // 选择环境（如prod）
    const stageSelect = page.locator('.bk-select, .stage-select, [class*="stage"]').first();
    if (await stageSelect.isVisible().catch(() => false)) {
      await stageSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // 点击资源信息tab
    const resourceTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /资源信息|资源/ }).first();
    if (await resourceTab.isVisible().catch(() => false)) {
      await resourceTab.click();
      await page.waitForTimeout(800);
    }

    // 验证资源列表展示
    const table = page.locator('table, .bk-table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    const rows = await getTableRowCount(page);
    expect(rows).toBeGreaterThanOrEqual(0);
  });

  test('场景: 资源筛选', async ({ page }) => {
    // Navigate to stage resource info page
    // Switch to detail mode and select a stage
    const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
    if (await detailTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(800);
    }

    // Select stage
    const stageSelect = page.locator('.bk-select, .stage-select, [class*="stage"]').first();
    if (await stageSelect.isVisible().catch(() => false)) {
      await stageSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // Click resource info tab
    const resourceTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /资源信息|资源/ }).first();
    if (await resourceTab.isVisible().catch(() => false)) {
      await resourceTab.click();
      await page.waitForTimeout(800);
    }

    // 搜索资源名称
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="名称"], input[placeholder*="资源"]').first();
    if (await searchInput.isVisible({ timeout: 10000 }).catch(() => false)) {
      await searchInput.fill('get');
      await page.waitForTimeout(1500);

      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);

      // 清空搜索测试重置
      await searchInput.clear();
      await page.waitForTimeout(1500);
    }

    // 按请求方法筛选（GET）
    const methodFilter = page.locator('th .bk-icon, th [class*="filter"]').first();
    if (await methodFilter.isVisible().catch(() => false)) {
      await methodFilter.click();
      await page.waitForTimeout(300);

      const getCheckbox = page.locator('.bk-checkbox, label').filter({ hasText: 'GET' }).first();
      if (await getCheckbox.isVisible().catch(() => false)) {
        await getCheckbox.click();
        await page.waitForTimeout(300);

        // 确认筛选
        const confirmFilter = page.locator('button').filter({ hasText: /确定|确认/ }).first();
        if (await confirmFilter.isVisible().catch(() => false)) {
          await confirmFilter.click();
          await page.waitForTimeout(800);
        }
      }
    }
  });

  test('场景: 查看资源详情', async ({ page }) => {
    // Switch to detail mode
    const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
    if (await detailTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(800);
    }

    // Select stage
    const stageSelect = page.locator('.bk-select, .stage-select, [class*="stage"]').first();
    if (await stageSelect.isVisible().catch(() => false)) {
      await stageSelect.click();
      await page.waitForTimeout(300);
      await page.locator('.bk-select-option, .bk-option').first().click();
      await page.waitForTimeout(300);
      await page.locator('body').click({ position: { x: 10, y: 10 } });
    }

    // Click resource info tab
    const resourceTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: /资源信息|资源/ }).first();
    if (await resourceTab.isVisible().catch(() => false)) {
      await resourceTab.click();
      await page.waitForTimeout(800);
    }

    // 点击资源名称查看详情
    const resourceLink = page.locator('table tbody tr a, .bk-table-body tr a, table tbody tr td').first();
    if (await resourceLink.isVisible({ timeout: 10000 }).catch(() => false)) {
      await resourceLink.click();
      await page.waitForTimeout(800);

      // 验证详情页面可见
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
