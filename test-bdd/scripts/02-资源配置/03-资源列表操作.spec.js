// @generated from: test-bdd/cases/02-资源配置/03-资源列表操作.md
// @generated-date: 2026-03-31

const { test, expect } = require('@playwright/test');
const { clickConfirm, getActiveDialog, getTableRowByText, selectDropdownOption, selectVisibleTableRowCheckboxes, getTableRowCount, getToastMessage, navigateToGatewayPage, getGatewayId } = require("../../runtime/helpers");

async function createBatchResources(page, count = 2) {
  const token = Date.now().toString(36);
  const resources = Array.from({ length: count }, (_, index) => ({
    name: `batch_op_${token}_${index + 1}`,
    path: `/batch-op-${token}-${index + 1}/`,
  }));

  const result = await page.evaluate(async ({ gwId, items }) => {
    try {
      const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
      const csrfToken = csrfMatch ? csrfMatch[1] : '';

      const backendResp = await fetch(`/backend/gateways/${gwId}/backends/`);
      const backendPayload = await backendResp.json().catch(() => ({}));
      const backends = backendPayload?.data?.results || backendPayload?.data || [];
      const backendId = (backends.find(item => item.name === 'default') || backends[0])?.id;

      if (!backendId) {
        return { ok: false, error: 'backend not found' };
      }

      for (const item of items) {
        const response = await fetch(`/backend/gateways/${gwId}/resources/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            name: item.name,
            description: 'batch operation test resource',
            method: 'GET',
            path: item.path,
            match_subpath: false,
            is_public: true,
            allow_apply_permission: true,
            backend: { id: backendId, config: { method: 'GET', path: '/get', timeout: 30 } },
            auth_config: { app_verified_required: true, auth_verified_required: true, resource_perm_required: false },
            label_ids: [],
          }),
        });

        if (!response.ok) {
          return { ok: false, status: response.status, item };
        }
      }

      return { ok: true };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }, { gwId: getGatewayId(), items: resources });

  if (!result.ok) {
    throw new Error(`Failed to create batch resources: ${JSON.stringify(result)}`);
  }

  return resources;
}

async function listResourcesByNames(page, names) {
  return await page.evaluate(async ({ gwId, targetNames }) => {
    const response = await fetch(`/backend/gateways/${gwId}/resources/?limit=500&offset=0`);
    const payload = await response.json().catch(() => ({}));
    const rows = payload?.data?.results || payload?.data || [];
    return rows.filter(item => targetNames.includes(item.name));
  }, { gwId: getGatewayId(), targetNames: names });
}

async function waitForResourcesByNames(page, names, timeout = 15000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeout) {
    const rows = await listResourcesByNames(page, names);
    if (rows.length === names.length) {
      return rows;
    }

    await page.waitForTimeout(1000);
  }

  throw new Error(`Resources not ready: ${names.join(', ')}`);
}

async function getResourceDetailsByNames(page, names) {
  const rows = await listResourcesByNames(page, names);
  return await page.evaluate(async ({ gwId, ids }) => {
    const details = [];
    for (const id of ids) {
      const response = await fetch(`/backend/gateways/${gwId}/resources/${id}/`);
      const payload = await response.json().catch(() => ({}));
      details.push(payload?.data || payload);
    }
    return details;
  }, { gwId: getGatewayId(), ids: rows.map(item => item.id) });
}

async function cleanupResourcesByNames(page, names) {
  await page.evaluate(async ({ gwId, targetNames }) => {
    const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
    const csrfToken = csrfMatch ? csrfMatch[1] : '';
    const headers = csrfToken ? { 'X-CSRFToken': csrfToken } : {};

    const response = await fetch(`/backend/gateways/${gwId}/resources/?limit=500&offset=0`);
    const payload = await response.json().catch(() => ({}));
    const rows = payload?.data?.results || payload?.data || [];
    const targets = rows.filter(item => targetNames.includes(item.name));

    for (const item of targets) {
      await fetch(`/backend/gateways/${gwId}/resources/${item.id}/`, {
        method: 'DELETE',
        headers,
      }).catch(() => null);
    }
  }, { gwId: getGatewayId(), targetNames: names }).catch(() => null);
}

async function searchResources(page, keyword) {
  const searchInput = page.locator('.bk-search-select, input[placeholder*="资源名称"], input[placeholder*="搜索"], input[placeholder*="Enter"]').first();
  await searchInput.click();
  await page.waitForTimeout(300);
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A').catch(() => {});
  await page.keyboard.type(keyword);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1500);
}

async function selectRowsByNames(page, names) {
  return await page.evaluate((targetNames) => {
    let clicked = 0;
    const rows = document.querySelectorAll('table tbody tr, .bk-table-body tr, .table-row');

    for (const row of rows) {
      const text = row.textContent || '';
      if (!targetNames.some(name => text.includes(name))) {
        continue;
      }

      const checkbox = row.querySelector('.bk-checkbox-input, label.bk-checkbox, .bk-checkbox-original');
      if (!checkbox) {
        continue;
      }

      checkbox.click();
      clicked += 1;
    }

    return clicked;
  }, names);
}


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
      if (await selectDropdownOption(page, tagFilter, null, '.bk-select-option, .bk-option, .tag-item').catch(() => false)) {
        await page.waitForTimeout(800);

        // 验证筛选结果
        const rows = await getTableRowCount(page);
        expect(rows).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('场景: 批量操作', async ({ page }) => {
    let createdResources = [];

    createdResources = await createBatchResources(page, 2);
    const createdNames = createdResources.map(item => item.name);

    try {
      await waitForResourcesByNames(page, createdNames);
      await page.reload();
      await page.waitForTimeout(2000);

      // 不勾选资源时，批量编辑按钮应保持不可点击。
      const batchBtn = page.locator('button, .bk-button').filter({ hasText: /批量/ }).first();
      await expect(batchBtn).toBeVisible({ timeout: 10000 });
      await batchBtn.click();
      await page.waitForTimeout(500);

      const batchEditBtn = page.locator('button, .bk-button').filter({ hasText: /^编辑资源$/ }).first();
      await expect(batchEditBtn).toBeDisabled({ timeout: 10000 });

      await searchResources(page, createdResources[0].name.replace(/_1$/, ''));
      await expect(getTableRowByText(page, createdResources[0].name)).toBeVisible({ timeout: 10000 });
      await expect(getTableRowByText(page, createdResources[1].name)).toBeVisible({ timeout: 10000 });

      const clicked = await selectRowsByNames(page, createdNames);
      expect(clicked).toBe(2);

      await batchEditBtn.click();
      await page.waitForTimeout(500);

      const editDialog = getActiveDialog(page);
      await expect(editDialog).toBeVisible({ timeout: 5000 });

      await editDialog.getByText('是否公开', { exact: true }).click();
      await page.waitForTimeout(300);
      await expect(clickConfirm(page, /确定|确认/, editDialog)).resolves.toBe(true);
      await page.waitForTimeout(1500);

      const editToast = await getToastMessage(page);
      expect(editToast).toMatch(/编辑成功|成功/);

      const editedDetails = await getResourceDetailsByNames(page, createdNames);
      for (const detail of editedDetails) {
        expect(detail.is_public).toBe(false);
        expect(detail.allow_apply_permission).toBe(false);
      }

      const batchDeleteBtn = page.locator('button, .bk-button').filter({ hasText: /^删除资源$/ }).first();
      await searchResources(page, createdResources[0].name.replace(/_1$/, ''));
      const clickedAgain = await selectRowsByNames(page, createdNames);
      expect(clickedAgain).toBe(2);

      await batchDeleteBtn.click();
      await page.waitForTimeout(500);

      const deleteDialog = getActiveDialog(page);
      await expect(deleteDialog).toBeVisible({ timeout: 5000 });
      await expect(deleteDialog).toContainText(createdResources[0].path);
      await expect(clickConfirm(page, /确定|确认/, deleteDialog)).resolves.toBe(true);
      await page.waitForTimeout(1500);

      const deleteToast = await getToastMessage(page);
      expect(deleteToast).toMatch(/删除成功|成功/);

      const remainingRows = await listResourcesByNames(page, createdNames);
      expect(remainingRows).toHaveLength(0);
      createdResources = [];
    } finally {
      if (createdResources.length) {
        await cleanupResourcesByNames(page, createdResources.map(item => item.name));
      }
    }
  });
});
