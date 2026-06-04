// @generated from: test-bdd/cases/02-资源配置/06-资源文档.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  cleanupResourceDocs,
  cleanupResourcesByName,
  createResourceDoc,
  createTestIdentifier,
  createTestResource,
  getDefaultBackend,
  getGatewayId,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiGet,
  pageApiPost,
  pageApiPut,
  unwrapApiData,
  unwrapApiResults,
} = require('../../runtime/helpers');

test.describe('功能: 资源配置 - 资源文档', () => {
  test('场景: 管理资源文档生命周期', async ({ page }) => {
    const gatewayId = getGatewayId();
    const resourceName = createTestIdentifier('bdd_doc_resource');
    let resource;
    let doc;

    await navigateToGatewayPage(page, gatewayId, '资源配置', '/resource/setting');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/resource/setting`));

    try {
      resource = await createTestResource(page, gatewayId, { name: resourceName });
      doc = await createResourceDoc(page, gatewayId, resource.id, {
        language: 'zh',
        content: `# ${resourceName}\n\nBDD resource document`,
      });

      let docs = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resources/${resource.id}/docs/`));
      let current = docs.find(item => item.id === doc.id);
      expect(current).toBeTruthy();
      expect(current.content).toContain(resourceName);

      await pageApiPut(page, `/gateways/${gatewayId}/resources/${resource.id}/docs/${doc.id}/`, {
        language: 'zh',
        content: `# ${resourceName}\n\nBDD resource document updated`,
      });

      docs = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resources/${resource.id}/docs/`));
      current = docs.find(item => item.id === doc.id);
      expect(current.content).toContain('updated');

      const backend = await getDefaultBackend(page, gatewayId);
      const preview = unwrapApiData(await pageApiPost(page, `/gateways/${gatewayId}/resources/import/doc/preview/`, {
        doc_language: 'zh',
        review_resource: {
          name: resource.name,
          description: resource.description,
          description_en: '',
          method: resource.method,
          path: resource.path,
          match_subpath: false,
          enable_websocket: false,
          is_public: true,
          allow_apply_permission: true,
          auth_config: {
            app_verified_required: true,
            auth_verified_required: true,
            resource_perm_required: false,
          },
          backend_name: backend.name,
          backend_config: {
            method: 'GET',
            path: '/get',
            match_subpath: false,
            timeout: 30,
          },
          labels: [],
          plugin_configs: [],
          openapi_schema: {},
        },
      }));
      expect(typeof preview.doc).toBe('string');

      const exportResp = await pageApiPost(page, `/gateways/${gatewayId}/docs/export/`, {
        export_type: 'selected',
        file_type: 'zip',
        resource_ids: [resource.id],
      }, { responseType: 'blob' });
      expect(exportResp.data.size).toBeGreaterThan(0);

      await pageApiDelete(page, `/gateways/${gatewayId}/resources/${resource.id}/docs/${doc.id}/`);
      doc = null;

      docs = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resources/${resource.id}/docs/`));
      expect(docs.some(item => item.id)).toBe(false);
    } finally {
      if (doc && resource) {
        await cleanupResourceDocs(page, gatewayId, resource.id);
      }
      await cleanupResourcesByName(page, gatewayId, resourceName);
    }
  });
});
