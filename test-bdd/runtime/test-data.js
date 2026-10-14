const { expect } = require('@playwright/test');
const {
  createTestIdentifier, createTestName, pageApiGet, pageApiPost,
  pageApiPut, pageApiDelete, unwrapApiData, unwrapApiResults,
} = require('./helpers');

async function createOwnedGateway(page, kind = 0) {
  const name = createTestName(kind === 2 ? 'bkai-bdd' : 'bdd-review');
  const response = await pageApiPost(page, '/gateways/', {
    name, description: 'BDD coverage review', maintainers: ['admin'],
    is_public: false, kind, gateway_type: 0, tenant_mode: 'single', tenant_id: 'default',
  });
  const id = unwrapApiData(response)?.id;
  expect(id, `Gateway creation did not return an ID: ${JSON.stringify(response)}`).toBeTruthy();
  return { id, name };
}

async function deleteOwnedGateway(page, gateway) {
  const detail = unwrapApiData(await pageApiGet(page, `/gateways/${gateway.id}/`));
  expect(detail.name, 'Refuse to delete a gateway not owned by this test').toBe(gateway.name);
  await pageApiPut(page, `/gateways/${gateway.id}/status/`, { status: 0 });
  await pageApiDelete(page, `/gateways/${gateway.id}/`);
  const remaining = unwrapApiResults(await pageApiGet(page, '/gateways/', { name: gateway.name, limit: 100 }));
  expect(remaining.some(row => String(row.id) === String(gateway.id)), 'Deleted gateway still exists').toBe(false);
}

async function createOwnedResource(page, gatewayId) {
  const name = createTestIdentifier('bdd_resource');
  const backends = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/backends/`));
  const backend = backends.find(row => row.name === 'default');
  expect(backend, 'Setup must provide a default backend').toBeTruthy();
  const payload = {
    name, description: 'BDD owned resource', method: 'GET', path: `/bdd/${name}/`,
    match_subpath: false, is_public: true, allow_apply_permission: true,
    backend: { id: backend.id, config: { method: 'GET', path: '/get', timeout: 30 } },
    auth_config: { app_verified_required: true, auth_verified_required: true, resource_perm_required: false },
    label_ids: [],
  };
  await pageApiPost(page, `/gateways/${gatewayId}/resources/`, payload);
  const resource = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resources/`, { name, limit: 100 }))
    .find(row => row.name === name);
  expect(resource, 'Created resource must be returned by list API').toBeTruthy();
  return { ...resource, payload };
}

module.exports = { createOwnedGateway, deleteOwnedGateway, createOwnedResource };
