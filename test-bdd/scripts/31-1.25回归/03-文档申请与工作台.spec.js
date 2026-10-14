// @generated from: test-bdd/cases/31-1.25回归/03-文档申请与工作台.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const {
  BASE_URL, getGatewayId, pageApiGet, pageApiPut, pageApiPost, pageApiDelete,
  unwrapApiData, unwrapApiResults, createTestVersion, getActiveDialog, getActiveSideslider,
} = require('../../runtime/helpers');
const { createOwnedResource } = require('../../runtime/test-data');
const base = BASE_URL.replace(/\/$/, '');
const appliedPath = '/me/workbench/permissions/gateway/applied/';

test.describe('功能: 1.25 文档申请与工作台', () => {
  // Empty/no-match app selection can emit this validation event. Submission,
  // ownership, cancellation, and deletion are all asserted independently below.
  test.use({ expectedPageErrors: ['请选择应用'] });
  test('场景: 文档中心选择搜索我的应用并申请撤销删除', async ({ page }, testInfo) => {
    test.setTimeout(150000);
    await page.goto(BASE_URL);
    const apps = unwrapApiData(await pageApiGet(page, '/me/applications/'));
    test.skip(!apps.length, '当前用户没有应用，不能验证真实申请流程');
    const app = apps[0];
    const gatewayId = getGatewayId();
    const gateway = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/`));
    const resource = await createOwnedResource(page, gatewayId);
    let application;
    let deleted = false;
    const applications = async () => unwrapApiResults(await pageApiGet(page, appliedPath, {
      bk_app_code: app.bk_app_code, limit: 10000,
    }));
    const findOwnedApplication = rows => rows.find(row => String(row.gateway_id) === String(gatewayId)
      && row.bk_app_code === app.bk_app_code && row.resources.some(r => r.id === resource.id));
    try {
      await pageApiPut(page, `/gateways/${gatewayId}/`, {
        description: gateway.description, is_public: true, maintainers: gateway.maintainers,
      });
      await pageApiPut(page, `/gateways/${gatewayId}/resources/${resource.id}/`, {
        ...resource.payload, enable_websocket: false,
        auth_config: { ...resource.payload.auth_config, resource_perm_required: true },
      });
      const version = await createTestVersion(page, gatewayId, { createResource: false });
      const stages = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/stages/`));
      const stage = stages.find(s => s.name === 'prod');
      expect(stage).toBeTruthy();
      await pageApiPost(page, `/gateways/${gatewayId}/releases/`, {
        stage_id: stage.id, resource_version_id: version.id, comment: 'BDD125 docs permission flow',
      });
      await expect.poll(async () => {
        const current = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/stages/`)).find(s => s.id === stage.id);
        return { status: current.release.status, version: current.resource_version.id };
      }, { timeout: 30000 }).toEqual({ status: 'success', version: version.id });
      await page.goto(`${base}/docs/api-docs/gateway/${gateway.name}?apiName=${resource.name}`);
      await page.getByRole('button', { name: '申请权限', exact: true }).click();
      const dialog = getActiveDialog(page);
      await dialog.getByPlaceholder('请选择要申请权限的应用').click();
      const search = page.getByPlaceholder('请输入关键字', { exact: true }).filter({ visible: true });
      await search.fill(`bdd125-no-app-${Date.now()}`);
      await expect(page.locator('.bk-select-option:visible')).toHaveCount(0);
      await search.fill(app.bk_app_code);
      await page.getByText(`${app.name} (${app.bk_app_code})`, { exact: true }).filter({ visible: true }).click();
      const submitted = page.waitForResponse(r => r.url().endsWith(`/docs/gateways/${gateway.name}/permissions/apply/`)
        && r.request().method() === 'POST');
      await dialog.getByRole('button', { name: '确定', exact: true }).click();
      const response = await submitted;
      expect(response.ok(), await response.text()).toBe(true);
      expect(response.request().postDataJSON()).toMatchObject({ bk_app_code: app.bk_app_code, resource_name: resource.name });
      await expect.poll(async () => findOwnedApplication(await applications())?.status).toBe('pending');
      application = findOwnedApplication(await applications());
      expect(application.applied_by).toBe('admin');
      await testInfo.attach('owned-application', {
        body: JSON.stringify({ id: application.id, gatewayId, resourceId: resource.id, app: app.bk_app_code }),
        contentType: 'application/json',
      });
      await page.goto(`${base}/personal-workbench/my-apply`);
      const row = page.getByRole('row').filter({ hasText: gateway.name }).filter({ hasText: app.bk_app_code });
      await row.getByRole('button', { name: '撤销', exact: true }).click();
      const cancelled = page.waitForResponse(r => r.url().endsWith(`${appliedPath}${application.id}/cancel/`)
        && r.request().method() === 'POST');
      await getActiveDialog(page).getByRole('button', { name: '撤销', exact: true }).click();
      expect((await cancelled).ok()).toBe(true);
      await expect(row).toContainText('已撤销');
      await page.reload();
      await expect(row).toContainText('已撤销');
      application = findOwnedApplication(await applications());
      expect(application.status).toBe('canceled');
      // The deployed site supports an ITSM tab and a local detail drawer.
      // Require one verified outcome; absence of both is a failure.
      const popup = page.waitForEvent('popup', { timeout: 5000 });
      const openedDetail = Promise.any([
        popup.then(async ticket => {
          expect(application.itsm_ticket_url).toBeTruthy();
          await expect.poll(() => ticket.url()).toBe(application.itsm_ticket_url);
          await ticket.close();
          return 'itsm';
        }),
        (async () => {
          const detail = getActiveSideslider(page);
          await expect(detail).toBeVisible();
          await expect(detail).toContainText(app.bk_app_code);
          await detail.locator('.bk-sideslider-close').click();
          return 'local';
        })(),
      ]);
      const [, detailMode] = await Promise.all([
        row.getByRole('button', { name: '详情', exact: true }).click(), openedDetail,
      ]);
      await testInfo.attach('application-detail-mode', { body: detailMode, contentType: 'text/plain' });
      await row.getByRole('button', { name: '删除', exact: true }).click();
      const removed = page.waitForResponse(r => r.url().endsWith(`${appliedPath}${application.id}/`) && r.request().method() === 'DELETE');
      await getActiveDialog(page).getByRole('button', { name: '删除', exact: true }).click();
      expect((await removed).status()).toBe(204);
      deleted = true;
      await expect(row).toHaveCount(0);
      expect((await applications()).some(r => r.id === application.id)).toBe(false);
    } catch (error) {
      await testInfo.attach('permission-workflow-error', { body: error.stack || String(error), contentType: 'text/plain' });
      throw error;
    } finally {
      // Cancellation changes the persisted status. Refresh before cleanup so a
      // later assertion failure never replays cancel against the stale record.
      application = findOwnedApplication(await applications());
      if (application && !deleted) {
        expect(String(application.gateway_id)).toBe(String(gatewayId));
        expect(application.resources.some(r => r.id === resource.id)).toBe(true);
        if (application.status === 'pending') await pageApiPost(page, `${appliedPath}${application.id}/cancel/`);
        await pageApiDelete(page, `${appliedPath}${application.id}/`);
      }
      await pageApiDelete(page, `/gateways/${gatewayId}/resources/${resource.id}/`);
      await pageApiPut(page, `/gateways/${gatewayId}/`, {
        description: gateway.description, is_public: gateway.is_public, maintainers: gateway.maintainers,
      });
    }
  });
});
