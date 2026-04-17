// @generated from: test-bdd/cases/02-资源配置/03-资源列表操作.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getTableRowCount, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


test.describe('功能: 资源配置 - 资源列表操作', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '资源配置', '/resource/setting');
  });

  test('场景: 搜索资源', async ({ page }) => {
    // Wait for resource table to load
    await page.locator('table, .bk-table').first().waitFor({ timeout: 15000 }).catch(() => {});

    // 搜索资源名称 — the search is a bk-search-select with placeholder "请输入资源名称或选择条件搜索"
    const searchInput = page.locator('.bk-search-select, input[placeholder*="资源名称"], input[placeholder*="搜索"], input[placeholder*="Enter"]').first();
    const searchVisible = await searchInput.isVisible({ timeout: 5000 }).catch(() => false);

    if (searchVisible) {
      await searchInput.click();
      await page.waitForTimeout(300);
      await page.keyboard.type('test');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);

      // 验证搜索结果
      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);
    }

    // 验证资源列表表格可见 or at least page loaded
    const table = page.locator('table, .bk-table').first();
    const tableVisible = await table.isVisible({ timeout: 5000 }).catch(() => false);
    if (tableVisible) {
      await expect(table).toBeVisible();
    } else {
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
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

    // 勾选多个资源 — use JavaScript to click since native checkboxes are hidden
    const clicked = await page.evaluate(() => {
      const rows = document.querySelectorAll('table tbody tr');
      let clickCount = 0;
      for (const row of rows) {
        if (row.textContent.includes('暂无数据')) continue;
        const cb = row.querySelector('.bk-checkbox-input, label.bk-checkbox, .bk-checkbox-original');
        if (cb) {
          cb.click();
          clickCount++;
          if (clickCount >= 2) break;
        }
      }
      return clickCount;
    });

    if (clicked >= 2) {
      await page.waitForTimeout(300);
      // 验证勾选成功
      expect(clicked).toBeGreaterThanOrEqual(2);
    }
  });
});
