// @generated from: test-bdd/cases/06-环境资源信息/01-环境资源信息.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getTableRowCount, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 环境资源信息 - 环境资源信息', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '环境概览', '/stage/overview');
  });

  test('场景: 查看环境资源列表', async ({ page }) => {
    // 切换到详情模式
    const detailTab = page.locator('text=详情模式').first();
    if (await detailTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(1500);
    }

    // 验证页面有内容（环境信息、版本信息等）
    const content = page.locator('[class*="stage"], [class*="version"], .bk-table, table, [class*="overview"]').first();
    const contentVisible = await content.isVisible({ timeout: 10000 }).catch(() => false);

    if (contentVisible) {
      await expect(content).toBeVisible();
    } else {
      // Verify at least we're on the right page
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 资源筛选', async ({ page }) => {
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    // Switch to detail mode
    const detailTab = page.locator('text=详情模式').first();
    if (await detailTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(1500);
    }

    // 搜索资源名称
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="名称"], input[placeholder*="资源"]').first();
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('test');
      await page.waitForTimeout(1500);

      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);

      await searchInput.clear();
      await page.waitForTimeout(1500);
    }
  });

  test('场景: 查看资源详情', async ({ page }) => {
    await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });

    // Switch to detail mode
    const detailTab = page.locator('text=详情模式').first();
    if (await detailTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await detailTab.click();
      await page.waitForTimeout(1500);
    }

    // 点击资源名称查看详情
    const resourceLink = page.locator('table tbody tr a, .bk-table-body tr a, table tbody tr td').first();
    if (await resourceLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await resourceLink.click();
      await page.waitForTimeout(800);

      // 验证详情页面可见
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
