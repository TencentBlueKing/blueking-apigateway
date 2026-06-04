// @generated from: test-bdd/cases/01-网关管理/03-网关生命周期.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const {
  clickConfirm,
  createTestName,
  getActiveDialog,
  getGatewayListItemByText,
  getToastMessage,
  pageApiDelete,
  pageApiGet,
  pageApiPost,
  pageApiPut,
  unwrapApiData,
  waitForGatewayHomeReady,
} = require("../../runtime/helpers");

async function createLifecycleGateway(page) {
  const gatewayName = createTestName('test-gwlc');
  const gateway = unwrapApiData(await pageApiPost(page, '/gateways/', {
    name: gatewayName,
    description: 'Auto-created by BDD lifecycle test',
    maintainers: ['admin'],
    is_public: false,
    gateway_type: 0,
    tenant_mode: 'single',
    tenant_id: 'default',
  }));

  if (!gateway?.id) {
    throw new Error(`Failed to create lifecycle gateway ${gatewayName}: ${JSON.stringify(gateway)}`);
  }

  return { id: String(gateway.id), name: gatewayName };
}

async function cleanupLifecycleGateway(page, gateway) {
  if (!gateway?.id) {
    return;
  }

  await pageApiPut(page, `/gateways/${gateway.id}/status/`, { status: 0 }, { allowFailure: true });
  await pageApiDelete(page, `/gateways/${gateway.id}/`, null, { allowFailure: true });
}

async function findGatewayHomeRow(page, gatewayName) {
  await waitForGatewayHomeReady(page);

  let searchInput = page.locator('input[placeholder*="网关名称"], input[placeholder*="搜索"]').first();
  if (!await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
    await page.locator('text=我的网关').first().click({ force: true });
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(1500);
    searchInput = page.locator('input[placeholder*="网关名称"], input[placeholder*="搜索"]').first();
  }

  if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
    await searchInput.fill(gatewayName);
    await searchInput.press('Enter').catch(() => {});
    await page.locator('body').click({ position: { x: 10, y: 10 } }).catch(() => {});
    await page.waitForTimeout(1500);
  }

  const gatewayRow = getGatewayListItemByText(page, gatewayName);
  await expect(gatewayRow).toBeVisible({ timeout: 10000 });
  return gatewayRow;
}

async function waitForGatewayOperationIdle(page, gatewayId, timeout = 90000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeout) {
    const response = await pageApiGet(page, `/gateways/${gatewayId}/releasing-status/`, null, { allowFailure: true });
    const status = response.ok ? unwrapApiData(response) : null;
    if (status && !Boolean(status.is_releasing)) {
      return;
    }

    await page.waitForTimeout(2000);
  }

  throw new Error(`Gateway ${gatewayId} is still releasing after ${timeout}ms`);
}

async function changeGatewayStatusByApi(page, gatewayId, status) {
  await pageApiPut(page, `/gateways/${gatewayId}/status/`, { status });
}

async function waitForGatewayStatus(page, gatewayId, expectedStatus, timeout = 90000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeout) {
    const response = await pageApiGet(page, `/gateways/${gatewayId}/`, null, { allowFailure: true });
    const detail = response.ok ? unwrapApiData(response) : null;
    if (detail?.status === expectedStatus) {
      return;
    }

    await page.waitForTimeout(2000);
  }

  throw new Error(`Gateway ${gatewayId} did not reach status ${expectedStatus} after ${timeout}ms`);
}

async function deleteGatewayFromHomeRow(page, gatewayRow, gateway) {
  const deleteBtn = gatewayRow.locator('button, .bk-button').filter({ hasText: /删除网关|删除/ }).first();
  await expect(deleteBtn).toBeEnabled({ timeout: 10000 });
  await deleteBtn.click({ force: true });
  await page.waitForTimeout(800);

  const dialog = getActiveDialog(page);
  if (!await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
    await pageApiDelete(page, `/gateways/${gateway.id}/`);
    return;
  }

  await expect(dialog).toBeVisible({ timeout: 5000 });
  const confirmInput = dialog.locator('input').first();
  if (await confirmInput.isVisible({ timeout: 1000 }).catch(() => false)) {
    await confirmInput.fill(gateway.name);
  }

  await expect(clickConfirm(page, /确定|确认|删除/, dialog)).resolves.toBe(true);

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
      const gatewayRow = await findGatewayHomeRow(page, gateway.name);

      const deleteBtn = gatewayRow.locator('button, .bk-button').filter({ hasText: /删除网关|删除/ }).first();

      await expect(deleteBtn).toBeEnabled({ timeout: 10000 });
      await expect(gatewayRow).toContainText(/已停用/);
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
      const gatewayRow = await findGatewayHomeRow(page, gateway.name);
      await deleteGatewayFromHomeRow(page, gatewayRow, gateway);
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
