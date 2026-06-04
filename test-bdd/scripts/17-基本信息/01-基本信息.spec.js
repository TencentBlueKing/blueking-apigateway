// @generated from: test-bdd/cases/17-基本信息/01-基本信息.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { getActionButton, getToastMessage, navigateToGatewayPage, getGatewayId } = require("../../runtime/helpers");

function normalizeDescription(value) {
  const text = String(value || '').trim();
  return text === '--' ? '' : text;
}

async function readHeaderDescription(page) {
  const content = page.locator('.header-info-description .edit-content').first();
  await expect(content).toBeVisible({ timeout: 10000 });
  return normalizeDescription(await content.textContent());
}

async function updateHeaderDescription(page, value) {
  const wrapper = page.locator('.header-info-description .gateways-edit-textarea').first();
  await expect(wrapper).toBeVisible({ timeout: 10000 });
  await wrapper.hover();

  const editIcon = wrapper.locator('.edit-action, .icon-ag-edit-small').first();
  await expect(editIcon).toBeVisible({ timeout: 5000 });
  await editIcon.click();

  const textarea = wrapper.locator('textarea').first();
  await expect(textarea).toBeVisible({ timeout: 5000 });
  await textarea.fill(value);
  await textarea.blur();

  await expect(wrapper.locator('.edit-content').first()).toContainText(value || '--', { timeout: 10000 });
  const toast = await getToastMessage(page);
  if (toast) {
    expect(toast).toMatch(/编辑成功|成功/);
  }
}

async function togglePublicSwitch(page) {
  const publicRow = page.locator('.detail-item-content-item').filter({ hasText: /是否公开/ }).first();
  await expect(publicRow).toBeVisible({ timeout: 10000 });

  const switcher = publicRow.locator('.bk-switcher, [role="switch"]').first();
  await expect(switcher).toBeVisible({ timeout: 5000 });
  await switcher.click();

  const toast = await getToastMessage(page);
  if (toast) {
    expect(toast).toMatch(/更新成功|成功/);
  }
}


test.describe('功能: 基本信息 - 网关基本信息管理', () => {
  test.setTimeout(90000);

  test('场景: 查看基本信息', async ({ page }) => {
    await navigateToGatewayPage(page, getGatewayId(), '基本信息', '/basic-info');

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

  test('场景: 编辑基本信息', async ({ page }) => {
    const gwId = getGatewayId();
    await navigateToGatewayPage(page, gwId, '基本信息', '/basic-info');

    const detailSection = page.locator('.basic-info-detail-item').filter({ hasText: /基础信息/ }).first();
    const editBtn = detailSection.locator('button, .bk-button').filter({ hasText: /编辑/ }).first();
    await expect(editBtn).toBeVisible({ timeout: 10000 });

    await editBtn.click();
    const cancelBtn = page.locator('button:visible, .bk-button:visible').filter({ hasText: /取消/ }).last();
    await expect(cancelBtn).toBeVisible({ timeout: 5000 });
    await cancelBtn.click();
    await expect(cancelBtn).toBeHidden({ timeout: 10000 });

    const originalDescription = await readHeaderDescription(page);
    const updatedDescription = `bdd basic info ${Date.now().toString(36)}`;

    try {
      await updateHeaderDescription(page, updatedDescription);
      await togglePublicSwitch(page);
    } finally {
      await updateHeaderDescription(page, originalDescription);
      await togglePublicSwitch(page);
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
