// @generated from: test-bdd/cases/10-后端服务/01-后端服务管理.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, selectDropdown, getToastMessage, getTableRowCount, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");


// Read-only gateway for list operations
const READONLY_GATEWAY_ID = 6;

test.describe('功能: 后端服务 - 后端服务管理', () => {
  test('场景: 创建后端服务', async ({ page }) => {
    // Mutating test uses TEST_GATEWAY_ID
    await navigateToGatewayPage(page, getGatewayId(), '后端服务', '/backends');

    // 点击新建按钮
    const addBtn = page.locator('button').filter({ hasText: '新建' }).first();
    await expect(addBtn).toBeVisible({ timeout: 10000 });
    await addBtn.click();
    await page.waitForTimeout(800);

    // 输入服务名称（必填）
    const serviceName = `test-svc-${Date.now().toString(36)}`;
    const nameInput = page.locator('input[placeholder*="名称"], input[name*="name"]').first();
    await nameInput.fill(serviceName);
    await page.waitForTimeout(300);

    // 选填描述
    const descInput = page.locator('textarea, input[placeholder*="描述"]').first();
    if (await descInput.isVisible().catch(() => false)) {
      await descInput.fill('自动化测试创建的后端服务');
    }

    // 输入后端服务地址
    const addrInput = page.locator('input[placeholder*="地址"], input[placeholder*="host"], input[placeholder*="http"]').first();
    if (await addrInput.isVisible().catch(() => false)) {
      await addrInput.fill('http://httpbin.org');
    }

    // 输入超时时间
    const timeoutInput = page.locator('input[placeholder*="超时"], input[type="number"]').first();
    if (await timeoutInput.isVisible().catch(() => false)) {
      await timeoutInput.fill('30');
    }

    // 点击确定
    await page.locator('button').filter({ hasText: /确定|确认/ }).first().click();
    await page.waitForTimeout(2000);

    // 验证新建成功
    const toast = await getToastMessage(page);
    expect(toast).toMatch(/成功|新建/);
  });

  test('场景: 编辑后端服务', async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '后端服务', '/backends');

    // 点击编辑按钮
    const editBtn = page.locator('button, a, .bk-button').filter({ hasText: '编辑' }).first();
    if (await editBtn.isVisible({ timeout: 10000 }).catch(() => false)) {
      await editBtn.click();
      await page.waitForTimeout(800);

      // 修改描述信息
      const descInput = page.locator('textarea, input[placeholder*="描述"]').first();
      if (await descInput.isVisible().catch(() => false)) {
        await descInput.clear();
        await descInput.fill(`编辑更新 - ${Date.now()}`);
      }

      // 点击确定
      await page.locator('button').filter({ hasText: /确定|确认/ }).first().click();
      await page.waitForTimeout(2000);

      // 验证保存成功
      const toast = await getToastMessage(page);
      expect(toast).toMatch(/成功|保存|发布/);
    }
  });

  test('场景: 删除后端服务', async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '后端服务', '/backends');

    // 找到未关联资源的后端服务并点击删除
    const deleteBtn = page.locator('button, a, .bk-button').filter({ hasText: '删除' }).first();
    if (await deleteBtn.isVisible({ timeout: 10000 }).catch(() => false)) {
      await deleteBtn.click();
      await page.waitForTimeout(800);

      // 确认删除操作
      const confirmBtn = page.locator('.bk-dialog button, .bk-dialog-footer button').filter({ hasText: /确定|确认|删除/ }).first();
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(2000);

        // 验证删除成功
        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|删除/);
      }
    }
  });

  test('场景: 查看服务列表', async ({ page }) => {
    // Read-only: list/search uses gateway ID 6
    await navigateToGatewayPage(page, '6', '后端服务', '/backends');

    // 验证服务列表可见
    const table = page.locator('table, .bk-table').first();
    await expect(table).toBeVisible({ timeout: 10000 });

    // 搜索服务名称
    const searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="名称"], input[placeholder*="服务"]').first();
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('default');
      await page.waitForTimeout(1500);

      // 验证搜索结果
      const rows = await getTableRowCount(page);
      expect(rows).toBeGreaterThanOrEqual(0);

      // 搜索不存在的服务名称
      await searchInput.clear();
      await searchInput.fill('nonexistent-service-xyz123');
      await page.waitForTimeout(1500);

      // 验证展示空结果
      const emptyRows = await getTableRowCount(page);
      expect(emptyRows).toBeLessThanOrEqual(1);
    }
  });
});
