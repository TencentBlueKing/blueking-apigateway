// @generated from: test-bdd/cases/01-网关管理/03-网关生命周期.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const {
  BASE_URL,
  clickConfirm,
  createTestName,
  getActiveDialog,
  getGatewayListItemByText,
  getToastMessage,
  navigateToGatewayPage,
  waitForGatewayHomeReady,
} = require("../../runtime/helpers");

async function createLifecycleGateway(page) {
  const gatewayName = createTestName('test-gwlc');

  const result = await page.evaluate(async (name) => {
    try {
      const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
      const csrfToken = csrfMatch ? csrfMatch[1] : '';

      const response = await fetch('/backend/gateways/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
          name,
          description: 'Auto-created by BDD lifecycle test',
          maintainers: ['admin'],
          is_public: false,
          gateway_type: 0,
          tenant_mode: 'single',
          tenant_id: 'default',
        }),
      });

      const data = await response.json().catch(() => ({}));
      return {
        ok: response.ok,
        status: response.status,
        id: data?.data?.id || null,
      };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }, gatewayName);

  if (!result.ok || !result.id) {
    throw new Error(`Failed to create lifecycle gateway ${gatewayName}: ${JSON.stringify(result)}`);
  }

  return { id: String(result.id), name: gatewayName };
}

async function cleanupLifecycleGateway(page, gateway) {
  if (!gateway?.id) {
    return;
  }

  await page.goto(BASE_URL);
  await page.waitForTimeout(800);

  await page.evaluate(async ({ gatewayId }) => {
    const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
    const csrfToken = csrfMatch ? csrfMatch[1] : '';

    try {
      await fetch(`/backend/gateways/${gatewayId}/status/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ status: 0 }),
      }).catch(() => null);

      await fetch(`/backend/gateways/${gatewayId}/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': csrfToken,
        },
      }).catch(() => null);
    } catch {
      // Ignore cleanup failures in test-local teardown.
    }
  }, { gatewayId: gateway.id });
}

function getDeleteGatewayButton(page) {
  return page.getByRole('button', { name: /^删除$/ }).first();
}

async function openGatewayBasicInfo(page, gatewayId, gatewayName) {
  await navigateToGatewayPage(page, gatewayId, '基本信息', '/basic-info');

  if (!await getDeleteGatewayButton(page).isVisible({ timeout: 3000 }).catch(() => false)) {
    await waitForGatewayHomeReady(page);

    const gatewayRow = getGatewayListItemByText(page, gatewayName);
    await expect(gatewayRow).toBeVisible({ timeout: 10000 });
    await gatewayRow.getByText(gatewayName, { exact: true }).click();
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(1500);

    const basicInfoMenu = page.locator('.bk-menu-item, [class*="menu"]').filter({ hasText: '基本信息' }).first();
    if (await basicInfoMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await basicInfoMenu.click();
      await page.waitForLoadState('networkidle').catch(() => {});
      await page.waitForTimeout(1500);
    } else {
      await navigateToGatewayPage(page, gatewayId, '基本信息', '/basic-info');
    }
  }

  await expect(page).toHaveURL(/basic-info/, { timeout: 10000 });
  await expect(getDeleteGatewayButton(page)).toBeVisible({ timeout: 10000 });
}

async function waitForGatewayOperationIdle(page, gatewayId, timeout = 90000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeout) {
    const status = await page.evaluate(async (id) => {
      try {
        const response = await fetch(`/backend/gateways/${id}/releasing-status/`);
        const data = await response.json().catch(() => ({}));
        return {
          ok: response.ok,
          isReleasing: Boolean(data?.data?.is_releasing ?? data?.is_releasing),
        };
      } catch (error) {
        return { ok: false, error: error.message };
      }
    }, gatewayId);

    if (status.ok && !status.isReleasing) {
      return;
    }

    await page.waitForTimeout(2000);
    await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForLoadState('networkidle').catch(() => {});
  }

  throw new Error(`Gateway ${gatewayId} is still releasing after ${timeout}ms`);
}

async function changeGatewayStatusByApi(page, gatewayId, status) {
  const result = await page.evaluate(async ({ id, nextStatus }) => {
    try {
      const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
      const csrfToken = csrfMatch ? csrfMatch[1] : '';
      const response = await fetch(`/backend/gateways/${id}/status/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ status: nextStatus }),
      });
      const data = await response.json().catch(() => ({}));
      return {
        ok: response.ok,
        status: response.status,
        data,
      };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }, { id: gatewayId, nextStatus: status });

  if (!result.ok) {
    throw new Error(`Failed to change gateway ${gatewayId} status to ${status}: ${JSON.stringify(result)}`);
  }
}

async function waitForGatewayStatus(page, gatewayId, expectedStatus, timeout = 90000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeout) {
    const detail = await page.evaluate(async (id) => {
      try {
        const response = await fetch(`/backend/gateways/${id}/`);
        const data = await response.json().catch(() => ({}));
        return {
          ok: response.ok,
          status: data?.data?.status,
        };
      } catch (error) {
        return { ok: false, error: error.message };
      }
    }, gatewayId);

    if (detail.ok && detail.status === expectedStatus) {
      return;
    }

    await page.waitForTimeout(2000);
  }

  throw new Error(`Gateway ${gatewayId} did not reach status ${expectedStatus} after ${timeout}ms`);
}

async function deleteGatewayFromBasicInfo(page, gatewayName) {
  const deleteBtn = getDeleteGatewayButton(page);
  await expect(deleteBtn).toBeEnabled({ timeout: 10000 });
  await deleteBtn.click();

  const dialog = getActiveDialog(page);
  const confirmInput = dialog.locator('input').first();
  await expect(confirmInput).toBeVisible({ timeout: 5000 });
  await confirmInput.fill(gatewayName);

  await expect(clickConfirm(page, /确定/, dialog)).resolves.toBe(true);

  const toast = await getToastMessage(page);
  expect(toast).toMatch(/删除成功|成功/);
}


test.describe('功能: 网关管理 - 网关生命周期', () => {
  test.setTimeout(120000);

  test.beforeEach(async ({ page }) => {
    await waitForGatewayHomeReady(page);
  });

  test('场景: 停用网关', async ({ page }) => {
    const gateway = await createLifecycleGateway(page);

    try {
      await changeGatewayStatusByApi(page, gateway.id, 0);
      await waitForGatewayOperationIdle(page, gateway.id);
      await waitForGatewayStatus(page, gateway.id, 0);
      await openGatewayBasicInfo(page, gateway.id, gateway.name);

      const enableBtn = page.locator('button, .bk-button').filter({ hasText: /立即启用|启用/ }).first();
      const deleteBtn = page.locator('button, .bk-button').filter({ hasText: /^删除$/ }).first();
      const disabledTag = page.locator('text=已停用').last();

      await expect(enableBtn).toBeVisible({ timeout: 10000 });
      await expect(deleteBtn).toBeEnabled({ timeout: 10000 });
      await expect(disabledTag).toBeVisible({ timeout: 10000 });
    } finally {
      await cleanupLifecycleGateway(page, gateway);
    }
  });

  test('场景: 删除网关', async ({ page }) => {
    const gateway = await createLifecycleGateway(page);
    let deleted = false;

    try {
      await changeGatewayStatusByApi(page, gateway.id, 0);
      await waitForGatewayOperationIdle(page, gateway.id);
      await waitForGatewayStatus(page, gateway.id, 0);
      await openGatewayBasicInfo(page, gateway.id, gateway.name);
      await deleteGatewayFromBasicInfo(page, gateway.name);
      deleted = true;

      await waitForGatewayHomeReady(page);
      const searchInput = page.locator('input[placeholder*="网关名称"], input[placeholder*="搜索"]').first();
      await expect(searchInput).toBeVisible({ timeout: 10000 });
      await searchInput.fill(gateway.name);
      await searchInput.press('Enter').catch(() => {});
      await page.locator('body').click({ position: { x: 10, y: 10 } }).catch(() => {});
      await page.waitForTimeout(1500);

      await expect(getGatewayListItemByText(page, gateway.name)).toHaveCount(0);
    } finally {
      if (!deleted) {
        await cleanupLifecycleGateway(page, gateway);
      }
    }
  });
});
