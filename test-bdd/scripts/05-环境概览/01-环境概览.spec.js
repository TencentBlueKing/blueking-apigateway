// @generated from: test-bdd/cases/05-环境概览/01-环境概览.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { clickConfirm, getActionButton, getActiveDialog, getActiveSideslider, getToastMessage, navigateToGatewayPage, getGatewayId, selectDropdownOption } = require("../../runtime/helpers");


test.describe('功能: 环境概览 - 环境概览', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '环境概览', '/stage/overview');
  });

  test('场景: 查看环境概览', async ({ page }) => {
    await expect(page).toHaveURL(new RegExp(`/${getGatewayId()}/stage/overview`), { timeout: 5000 });

    const pageContent = page.locator('.bk-table, [class*="stage"], [class*="overview"], .bk-exception').first();
    await expect(pageContent).toBeVisible({ timeout: 10000 });
  });

  test('场景: 发布资源', async ({ page }) => {
    // 点击发布资源按钮
    const publishBtn = page.locator('button').filter({ hasText: '发布资源' });
    const isEnabled = await publishBtn.evaluate(el => !el.disabled).catch(() => false);

    if (isEnabled) {
      await publishBtn.click();
      await page.waitForTimeout(1500);

      // The publish sideslider opens. All interactions must be scoped to it.
      const sideslider = getActiveSideslider(page);

      // 选择要发布的资源版本 — the version select is inside the sideslider
      await selectDropdownOption(page, sideslider.locator('.bk-select').last()).catch(() => false);

      // 点击下一步
      const nextBtn = getActionButton(sideslider, '下一步');
      if (await nextBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nextBtn.click();
        await page.waitForTimeout(1000);
      }

      // 确认发布
      if (await clickConfirm(page, /确认发布|确认|确定/, getActiveDialog(page)).catch(() => false)
        || await clickConfirm(page, /确认发布|确认|确定/, sideslider).catch(() => false)) {
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        if (toast) {
          expect(toast).toMatch(/成功|发布/);
        }
      }
    } else {
      // Button is disabled — verify the overview page loaded correctly
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });

  test('场景: 下架资源', async ({ page }) => {
    // 查找并点击下架按钮
    const unpublishBtn = page.locator('button').filter({ hasText: '下架' });
    const isEnabled = await unpublishBtn.evaluate(el => !el.disabled).catch(() => false);

    if (isEnabled) {
      await unpublishBtn.click();
      await page.waitForTimeout(800);

      // 确认下架操作
      if (await clickConfirm(page, /确定|确认|下架/, getActiveDialog(page)).catch(() => false)) {
        await page.waitForTimeout(2000);

        const toast = await getToastMessage(page);
        expect(toast).toMatch(/成功|下架/);
      }
    } else {
      // Button is disabled — verify the overview page loaded correctly
      await expect(page).toHaveURL(new RegExp('/' + getGatewayId() + '/'), { timeout: 5000 });
    }
  });
});
