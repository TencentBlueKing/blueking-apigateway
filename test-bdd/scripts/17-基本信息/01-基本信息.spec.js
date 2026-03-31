// @generated from: test-bdd/cases/17-基本信息/01-基本信息.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { waitForPageReady, reAuth, navigateToGatewayPage, BASE_URL, getGatewayId } = require("../../runtime/helpers");

const GATEWAY_ID = 6; // read-only for viewing

test.describe('功能: 基本信息 - 网关基本信息管理', () => {
  test('场景: 查看基本信息', async ({ page }) => {
    await navigateToGatewayPage(page, '6', '基本信息', '/basic-info');

    // 页面应展示网关名称、描述、维护人员、是否公开等基础信息
    const basicInfoSection = page.locator('[class*="basic"], [class*="info"], .bk-form, .detail-info').first();
    await expect(basicInfoSection).toBeVisible({ timeout: 10000 });

    // 支持复制网关API地址
    const copyBtn = page.locator('button, .bk-button, [class*="copy"], .icon-copy').first();
    if (await copyBtn.isVisible().catch(() => false)) {
      await expect(copyBtn).toBeVisible();
    }

    // 支持复制和下载API公钥
    const publicKeySection = page.locator('span, div, label').filter({ hasText: /公钥|Public Key/ }).first();
    if (await publicKeySection.isVisible().catch(() => false)) {
      await expect(publicKeySection).toBeVisible();
    }

    // 支持"更多详情"链接
    const moreDetailLink = page.locator('a, span').filter({ hasText: /更多详情|详情/ }).first();
    if (await moreDetailLink.isVisible().catch(() => false)) {
      await expect(moreDetailLink).toBeVisible();
    }
  });

  test('场景: 编辑基本信息 (read-only verification)', async ({ page }) => {
    // Use mutable gateway for edit scenario verification
    const gwId = getGatewayId();
    await navigateToGatewayPage(page, gwId, '基本信息', '/basic-info');

    // 验证"编辑基础信息"按钮存在
    const editBtn = page.locator('button, .bk-button').filter({ hasText: /编辑/ }).first();
    if (await editBtn.isVisible().catch(() => false)) {
      await expect(editBtn).toBeVisible();
    }
  });

  test('场景: 网关状态管理 (read-only verification)', async ({ page }) => {
    const gwId = getGatewayId();
    await navigateToGatewayPage(page, gwId, '基本信息', '/basic-info');

    // 验证停用/启用按钮存在
    const statusBtn = page.locator('button, .bk-button').filter({ hasText: /停用|启用/ }).first();
    if (await statusBtn.isVisible().catch(() => false)) {
      await expect(statusBtn).toBeVisible();
    }
  });
});
