// @generated from: test-bdd/cases/12-应用权限/01-应用权限.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  cleanupPermissionsByAppCode,
  cleanupResourcesByName,
  createGatewayPermission,
  createTestIdentifier,
  getGatewayId,
  listGatewayPermissions,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiPost,
} = require('../../runtime/helpers');

function splitPermissionIds(permissions) {
  return {
    gatewayIds: permissions.filter(item => item.grant_dimension === 'api').map(item => item.id),
    resourceIds: permissions.filter(item => item.grant_dimension === 'resource').map(item => item.id),
  };
}

test.describe('功能: 应用权限 - 应用权限管理', () => {
  test('场景: 主动授权、续期和删除应用权限', async ({ page }) => {
    const gatewayId = getGatewayId();
    const bkAppCode = `bddapp${Date.now().toString(36).slice(-8)}`;
    const resourceName = createTestIdentifier('bdd_perm_resource');
    let createdResourceName = resourceName;

    await navigateToGatewayPage(page, gatewayId, '应用权限', '/permission/app');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/permission/app`));

    try {
      const { resource } = await createGatewayPermission(page, gatewayId, {
        bkAppCode,
        resourceName,
        expireDays: 180,
      });
      createdResourceName = resource.name;

      let permissions = await listGatewayPermissions(page, gatewayId, bkAppCode);
      expect(permissions.map(item => item.bk_app_code)).toContain(bkAppCode);

      let { gatewayIds, resourceIds } = splitPermissionIds(permissions);
      expect(gatewayIds.length).toBeGreaterThan(0);
      expect(resourceIds.length).toBeGreaterThan(0);

      await pageApiPost(page, `/gateways/${gatewayId}/permissions/app-gateway-permissions/renew/`, {
        ids: gatewayIds,
        expire_days: 360,
      });

      permissions = await listGatewayPermissions(page, gatewayId, bkAppCode);
      const gatewayPermission = permissions.find(item => item.grant_dimension === 'api');
      expect(gatewayPermission).toBeTruthy();
      expect(Boolean(gatewayPermission.renewable)).toBe(false);

      ({ gatewayIds, resourceIds } = splitPermissionIds(permissions));
      await pageApiPost(page, `/gateways/${gatewayId}/permissions/app-permissions/renew/`, {
        gateway_dimension_ids: gatewayIds,
        resource_dimension_ids: resourceIds,
        expire_days: 360,
      });

      permissions = await listGatewayPermissions(page, gatewayId, bkAppCode);
      expect(permissions.length).toBeGreaterThanOrEqual(2);
      expect(permissions.every(item => Boolean(item.expires))).toBe(true);

      ({ gatewayIds, resourceIds } = splitPermissionIds(permissions));
      await pageApiDelete(page, `/gateways/${gatewayId}/permissions/app-resource-permissions/delete/`, { ids: resourceIds }, { query: true });
      await pageApiDelete(page, `/gateways/${gatewayId}/permissions/app-gateway-permissions/delete/`, { ids: gatewayIds }, { query: true });

      permissions = await listGatewayPermissions(page, gatewayId, bkAppCode);
      expect(permissions.length).toBe(0);
    } finally {
      await cleanupPermissionsByAppCode(page, gatewayId, bkAppCode);
      await cleanupResourcesByName(page, gatewayId, createdResourceName);
    }
  });

  test('场景: 权限筛选', async ({ page }) => {
    const gatewayId = getGatewayId();

    await navigateToGatewayPage(page, gatewayId, '应用权限', '/permission/app');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/permission/app`));

    const response = await listGatewayPermissions(page, gatewayId, '');
    expect(Array.isArray(response)).toBe(true);

    const tableOrEmpty = page.locator('.bk-table, .bk-exception, [class*="empty"]').first();
    await expect(tableOrEmpty).toBeVisible({ timeout: 10000 });
  });
});
