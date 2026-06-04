// @generated from: test-bdd/cases/03-资源版本/01-版本管理.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  cleanupResourceDocs,
  cleanupResourcesByName,
  cleanupVersionsByVersion,
  createResourceDoc,
  createTestIdentifier,
  createTestResource,
  createTestVersion,
  getGatewayId,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiGet,
  pageApiPost,
  unwrapApiResults,
} = require('../../runtime/helpers');

async function listVersions(page, gatewayId) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resource-versions/`));
}

test.describe('功能: 资源版本 - 版本管理', () => {
  test('场景: 生成版本、导出并删除单个版本', async ({ page }) => {
    const gatewayId = getGatewayId();
    const resourceName = createTestIdentifier('bdd_version_resource');
    let resource;
    let version;

    await navigateToGatewayPage(page, gatewayId, '资源版本', '/resource/version');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/resource/version`));

    try {
      resource = await createTestResource(page, gatewayId, { name: resourceName });
      await createResourceDoc(page, gatewayId, resource.id, {
        language: 'zh',
        content: `# ${resourceName}\n\nversion doc`,
      });
      version = await createTestVersion(page, gatewayId, { createResource: false });

      let versions = await listVersions(page, gatewayId);
      expect(versions.some(item => item.id === version.id)).toBe(true);

      const versionExport = await pageApiPost(page, `/gateways/${gatewayId}/resource-versions/${version.id}/export/`, {
        file_type: 'yaml',
      }, { responseType: 'blob' });
      expect(versionExport.data.size).toBeGreaterThan(0);

      const docsExport = await pageApiPost(page, `/gateways/${gatewayId}/resource-versions/${version.id}/export-docs/`, {
        file_type: 'zip',
      }, { responseType: 'blob' });
      expect(docsExport.data.size).toBeGreaterThan(0);

      const deletedVersionId = version.id;
      await pageApiDelete(page, `/gateways/${gatewayId}/resource-versions/${version.id}/`);
      version = null;

      versions = await listVersions(page, gatewayId);
      expect(versions.some(item => item.id === deletedVersionId)).toBe(false);
    } finally {
      if (version) {
        await cleanupVersionsByVersion(page, gatewayId, version.version);
      }
      if (resource) {
        await cleanupResourceDocs(page, gatewayId, resource.id);
      }
      await cleanupResourcesByName(page, gatewayId, resourceName);
    }
  });

  test('场景: 批量删除未发布版本', async ({ page }) => {
    const gatewayId = getGatewayId();
    const resourceNames = [
      createTestIdentifier('bdd_batch_version_a'),
      createTestIdentifier('bdd_batch_version_b'),
    ];
    const resources = [];
    const versions = [];

    await navigateToGatewayPage(page, gatewayId, '资源版本', '/resource/version');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/resource/version`));

    try {
      for (const resourceName of resourceNames) {
        const resource = await createTestResource(page, gatewayId, { name: resourceName });
        resources.push(resource);
        await createResourceDoc(page, gatewayId, resource.id, {
          language: 'zh',
          content: `# ${resourceName}\n\nbatch version doc`,
        });
        versions.push(await createTestVersion(page, gatewayId, { createResource: false }));
      }

      let existingVersions = await listVersions(page, gatewayId);
      for (const version of versions) {
        expect(existingVersions.some(item => item.id === version.id)).toBe(true);
      }

      const deletedVersionIds = versions.map(item => item.id);
      await pageApiDelete(page, `/gateways/${gatewayId}/resource-versions/batch/`, { ids: deletedVersionIds });
      versions.length = 0;

      existingVersions = await listVersions(page, gatewayId);
      expect(existingVersions.some(item => deletedVersionIds.includes(item.id))).toBe(false);
    } finally {
      await cleanupVersionsByVersion(page, gatewayId, versions.map(item => item.version));
      for (const resource of resources) {
        await cleanupResourceDocs(page, gatewayId, resource.id);
      }
      await cleanupResourcesByName(page, gatewayId, resourceNames);
    }
  });
});
