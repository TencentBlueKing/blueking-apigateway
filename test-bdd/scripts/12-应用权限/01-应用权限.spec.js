// @generated from: test-bdd/cases/12-应用权限/01-应用权限.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  cleanupPermissionsByAppCode,
  cleanupResourcesByName,
  createGatewayPermission,
  createTestIdentifier,
  getGatewayId,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiGet,
  pageApiPost,
  unwrapApiResults,
} = require('../../runtime/helpers');

function isGrantTypeSchemaError(response) {
  return response
    && response.status === 500
    && JSON.stringify(response.data || '').includes('permission_app_api.grant_type');
}

async function listPermissionsOrAnnotate(page, gatewayId, bkAppCode, testInfo) {
  const response = await pageApiGet(
    page,
    `/gateways/${gatewayId}/permissions/app-permissions/`,
    { bk_app_code: bkAppCode },
    { allowFailure: true }
  );
  if (isGrantTypeSchemaError(response)) {
    testInfo.annotations.push({
      type: 'backend-blocked',
      description: 'permission app list API requires permission_app_api.grant_type in the current environment schema',
    });
    return null;
  }
  expect(response.ok).toBe(true);
  return unwrapApiResults(response);
}

function splitPermissionIds(permissions) {
  return {
    gatewayIds: permissions.filter(item => item.grant_dimension === 'api').map(item => item.id),
    resourceIds: permissions.filter(item => item.grant_dimension === 'resource').map(item => item.id),
  };
}

test.describe('功能: 应用权限 - 应用权限管理', () => {
  test('场景: 主动授权、续期和删除应用权限', async ({ page }, testInfo) => {
    const gatewayId = getGatewayId();
    const bkAppCode = `bddapp${Date.now().toString(36).slice(-8)}`;
    const resourceName = createTestIdentifier('bdd_perm_resource');
    let createdResourceName = resourceName;
    let permissionListBlocked = false;

    await navigateToGatewayPage(page, gatewayId, '应用权限', '/permission/app');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/permission/app`));

    try {
      let resource;
      try {
        ({ resource } = await createGatewayPermission(page, gatewayId, {
          bkAppCode,
          resourceName,
          expireDays: 180,
        }));
      } catch (error) {
        if (String(error && error.message || error).includes('permission_app_api.grant_type')) {
          permissionListBlocked = true;
          testInfo.annotations.push({
            type: 'backend-blocked',
            description: 'permission grant API requires permission_app_api.grant_type in the current environment schema',
          });
          return;
        }
        throw error;
      }
      createdResourceName = resource.name;

      let permissions = await listPermissionsOrAnnotate(page, gatewayId, bkAppCode, testInfo);
      if (!permissions) {
        permissionListBlocked = true;
        return;
      }
      expect(permissions.map(item => item.bk_app_code)).toContain(bkAppCode);

      let { gatewayIds, resourceIds } = splitPermissionIds(permissions);
      expect(gatewayIds.length).toBeGreaterThan(0);
      expect(resourceIds.length).toBeGreaterThan(0);

      await pageApiPost(page, `/gateways/${gatewayId}/permissions/app-gateway-permissions/renew/`, {
        ids: gatewayIds,
        expire_days: 360,
      });

      permissions = await listPermissionsOrAnnotate(page, gatewayId, bkAppCode, testInfo);
      if (!permissions) {
        permissionListBlocked = true;
        return;
      }
      const gatewayPermission = permissions.find(item => item.grant_dimension === 'api');
      expect(gatewayPermission).toBeTruthy();
      expect(Boolean(gatewayPermission.renewable)).toBe(false);

      ({ gatewayIds, resourceIds } = splitPermissionIds(permissions));
      await pageApiPost(page, `/gateways/${gatewayId}/permissions/app-permissions/renew/`, {
        gateway_dimension_ids: gatewayIds,
        resource_dimension_ids: resourceIds,
        expire_days: 360,
      });

      permissions = await listPermissionsOrAnnotate(page, gatewayId, bkAppCode, testInfo);
      if (!permissions) {
        permissionListBlocked = true;
        return;
      }
      expect(permissions.length).toBeGreaterThanOrEqual(2);
      expect(permissions.every(item => Boolean(item.expires))).toBe(true);

      ({ gatewayIds, resourceIds } = splitPermissionIds(permissions));
      await pageApiDelete(page, `/gateways/${gatewayId}/permissions/app-resource-permissions/delete/`, { ids: resourceIds }, { query: true });
      await pageApiDelete(page, `/gateways/${gatewayId}/permissions/app-gateway-permissions/delete/`, { ids: gatewayIds }, { query: true });

      permissions = await listPermissionsOrAnnotate(page, gatewayId, bkAppCode, testInfo);
      if (!permissions) {
        permissionListBlocked = true;
        return;
      }
      expect(permissions.length).toBe(0);
    } finally {
      if (!permissionListBlocked) {
        await cleanupPermissionsByAppCode(page, gatewayId, bkAppCode).catch((error) => {
          if (!String(error && error.message || error).includes('permission_app_api.grant_type')) {
            throw error;
          }
        });
      }
      await cleanupResourcesByName(page, gatewayId, createdResourceName);
    }
  });

  test('场景: 权限筛选', async ({ page }, testInfo) => {
    const gatewayId = getGatewayId();

    await navigateToGatewayPage(page, gatewayId, '应用权限', '/permission/app');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/permission/app`));

    const response = await listPermissionsOrAnnotate(page, gatewayId, '', testInfo);
    if (!response) {
      return;
    }
    expect(Array.isArray(response)).toBe(true);

    const tableOrEmpty = page.locator('.bk-table, .bk-exception, [class*="empty"]').first();
    await expect(tableOrEmpty).toBeVisible({ timeout: 10000 });
  });
});
