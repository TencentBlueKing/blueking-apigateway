// test-bdd/scripts/setup.js
// Global setup: authenticate, create test gateway, configure backend, create resource, publish
// This runs once before all tests via Playwright's globalSetup.

const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const { BASE_URL, USERNAME, PASSWORD, COOKIE } = require('./test-env');
const ENV_FILE = path.join(__dirname, '.env');

module.exports = async () => {
  if (!BASE_URL) {
    throw new Error('BASE_URL is empty — check "url" in .test-env.json');
  }
  if (!PASSWORD && !COOKIE) {
    throw new Error('Either PASSWORD or COOKIE must be set in .test-env.json');
  }

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // === Step 1: Authenticate ===
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);

    if (page.url().includes('/login/')) {
      if (COOKIE) {
        const domain = new URL(BASE_URL).hostname.split('.').slice(-2).join('.');
        await context.addCookies([{ name: 'bk_token', value: COOKIE, domain: '.' + domain, path: '/' }]);
        await page.goto(BASE_URL);
        await page.waitForTimeout(3000);
      } else {
        const hasChineseForm = await page.locator('input[placeholder="请输入用户名"]').isVisible().catch(() => false);
        if (hasChineseForm) {
          await page.locator('input[placeholder="请输入用户名"]').click();
          await page.locator('input[placeholder="请输入用户名"]').type(USERNAME);
          await page.locator('input[placeholder="请输入密码"]').click();
          await page.locator('input[placeholder="请输入密码"]').type(PASSWORD);
          await page.locator('button').filter({ hasText: '立即登录' }).click();
        } else {
          await page.locator('#user').click();
          await page.locator('#user').type(USERNAME);
          await page.locator('#password').click();
          await page.locator('#password').type(PASSWORD);
          await page.locator('.login-btn').click();
        }

        for (let i = 0; i < 30; i++) {
          await page.waitForTimeout(500);
          if (!page.url().includes('/login/')) break;
        }
      }

      if (page.url().includes('/login/')) {
        throw new Error('Setup: Authentication failed');
      }
    }

    console.log('[setup] Authenticated successfully');

    // === Step 2: Create test gateway via API ===
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    const testName = 'testagent' + Date.now().toString().slice(-6);

    const createResult = await page.evaluate(async (name) => {
      try {
        // Get CSRF token — try multiple cookie name patterns
        const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        const resp = await fetch('/backend/gateways/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            name: name,
            description: 'Auto-created by BDD test setup',
            maintainers: ['admin'],
            is_public: false,
            gateway_type: 0,
            tenant_mode: 'single',
            tenant_id: 'default',
          }),
        });
        const data = await resp.json();
        return { ok: resp.ok, status: resp.status, data };
      } catch(e) {
        return { error: e.message };
      }
    }, testName);

    console.log(`[setup] Create gateway result: ${JSON.stringify(createResult).substring(0, 200)}`);

    let gatewayId = null;
    if (createResult.ok && createResult.data?.data?.id) {
      gatewayId = String(createResult.data.data.id);
    } else if (createResult.data?.data?.id) {
      gatewayId = String(createResult.data.data.id);
    }

    // Fallback: look up via list API
    if (!gatewayId) {
      await page.waitForTimeout(2000);
      const lookupResult = await page.evaluate(async (name) => {
        try {
          const resp = await fetch('/backend/gateways/?limit=10000');
          const data = await resp.json();
          const gw = (data.data?.results || []).find(g => g.name === name);
          return gw ? { id: gw.id } : null;
        } catch(e) { return null; }
      }, testName);

      if (lookupResult?.id) {
        gatewayId = String(lookupResult.id);
      }
    }

    if (!gatewayId) {
      throw new Error(`Setup: Could not determine gateway ID for ${testName}`);
    }

    console.log(`[setup] Created test gateway: ${testName} (ID: ${gatewayId})`);

    // === Step 3: Configure backend service via API ===
    // First, navigate to the gateway page to get cookies/context
    await page.goto(`${BASE_URL}/${gatewayId}/stage/overview`);
    await page.waitForTimeout(3000);

    // Backend update requires stage_id for each config entry, and the name must
    // pass unique validation. We use the detail endpoint to get current state,
    // then update with correct format.
    const backendResult = await page.evaluate(async (gwId) => {
      try {
        const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        // Get stages
        const stageResp = await fetch(`/backend/gateways/${gwId}/stages/`);
        const stageData = await stageResp.json();
        const stages = stageData.data || [];

        // Get existing backends
        const listResp = await fetch(`/backend/gateways/${gwId}/backends/`);
        const listData = await listResp.json();
        const backends = listData.data?.results || listData.data || [];
        const defaultBackend = backends.find(b => b.name === 'default') || backends[0];

        if (!defaultBackend || stages.length === 0) {
          return { error: 'No backend or stages found', backends: backends.length, stages: stages.length };
        }

        // Get backend detail to see current config
        const detailResp = await fetch(`/backend/gateways/${gwId}/backends/${defaultBackend.id}/`);
        const detailData = await detailResp.json();
        const detail = detailData.data || detailData;

        // Build configs array — one entry per stage with httpbin.org address
        const configs = stages.map(stage => ({
          stage_id: stage.id,
          type: 'node',
          timeout: 30,
          loadbalance: 'roundrobin',
          hosts: [{ scheme: 'http', host: 'httpbin.org', weight: 100 }],
        }));

        const updateResp = await fetch(`/backend/gateways/${gwId}/backends/${defaultBackend.id}/`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            name: defaultBackend.name,
            description: defaultBackend.description || '',
            type: 'http',
            configs: configs,
          }),
        });
        const respText = await updateResp.text();
        let respData;
        try { respData = JSON.parse(respText); } catch(e) { respData = respText; }
        return { ok: updateResp.ok, status: updateResp.status, backendId: defaultBackend.id, detail: respData };
      } catch(e) {
        return { error: e.message };
      }
    }, gatewayId);

    console.log(`[setup] Backend service result: ${JSON.stringify(backendResult).substring(0, 800)}`);

    if (!backendResult.ok) {
      console.error(`[setup] CRITICAL: Backend update failed — resource edit will show 'please configure backend address'`);
    }

    // === Step 4: Create a test resource via API ===
    const resName = 'test_resource_' + Date.now().toString().slice(-4);
    const resourceResult = await page.evaluate(async ({ gwId, name }) => {
      try {
        const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        // Get default backend id
        const backendResp = await fetch(`/backend/gateways/${gwId}/backends/`);
        const backendData = await backendResp.json();
        const backends = backendData.data?.results || backendData.data || [];
        const defaultBackend = backends.find(b => b.name === 'default') || backends[0];
        const backendId = defaultBackend ? defaultBackend.id : null;

        // API expects: backend: {id, config: {method, path}}
        const resp = await fetch(`/backend/gateways/${gwId}/resources/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            name: name,
            description: 'Auto-created by BDD test setup',
            method: 'GET',
            path: `/test/${name}/`,
            match_subpath: false,
            is_public: true,
            allow_apply_permission: true,
            backend: {
              id: backendId,
              config: {
                method: 'GET',
                path: '/get',
                timeout: 30,
              },
            },
            auth_config: {
              app_verified_required: true,
              auth_verified_required: true,
              resource_perm_required: false,
            },
            label_ids: [],
          }),
        });
        const data = await resp.json();
        return { ok: resp.ok, status: resp.status, data };
      } catch(e) {
        return { error: e.message };
      }
    }, { gwId: gatewayId, name: resName });

    console.log(`[setup] Test resource created: ${JSON.stringify(resourceResult).substring(0, 200)}`);

    if (!resourceResult.ok) {
      console.error(`[setup] WARNING: Resource creation failed: ${JSON.stringify(resourceResult).substring(0, 500)}`);
    }

    // === Step 5: Generate resource version via API ===
    const versionResult = await page.evaluate(async (gwId) => {
      try {
        const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        // Get suggested next version first
        let version = '1.0.0';
        try {
          const nextResp = await fetch(`/backend/gateways/${gwId}/resource-versions/next-version/`);
          const nextData = await nextResp.json();
          if (nextData.data?.version) {
            version = nextData.data.version;
          }
        } catch(e) { /* use default */ }

        const resp = await fetch(`/backend/gateways/${gwId}/resource-versions/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            version: version,
            comment: 'BDD test version',
          }),
        });
        const data = await resp.json();
        return { ok: resp.ok, status: resp.status, data };
      } catch(e) {
        return { error: e.message };
      }
    }, gatewayId);

    console.log(`[setup] Resource version generated: ${JSON.stringify(versionResult).substring(0, 200)}`);

    if (!versionResult.ok) {
      console.error(`[setup] WARNING: Version generation failed: ${JSON.stringify(versionResult).substring(0, 500)}`);
    }

    // Get version ID for publishing — the create API returns no data,
    // so we must list versions to find the one we just created
    let versionId = null;
    if (versionResult.ok) {
      const versionListResult = await page.evaluate(async (gwId) => {
        try {
          const resp = await fetch(`/backend/gateways/${gwId}/resource-versions/?limit=1&offset=0`);
          const data = await resp.json();
          const versions = data.data?.results || data.data || [];
          return versions.length > 0 ? { id: versions[0].id } : null;
        } catch(e) { return null; }
      }, gatewayId);

      if (versionListResult?.id) {
        versionId = versionListResult.id;
      }
      console.log(`[setup] Version ID resolved: ${versionId}`);
    }

    // === Step 6: Get stage ID and publish ===
    if (versionId) {
      const publishResult = await page.evaluate(async ({ gwId, versnId }) => {
        try {
          const csrfMatch = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
          const csrfToken = csrfMatch ? csrfMatch[1] : '';

          // Get stages
          const stageResp = await fetch(`/backend/gateways/${gwId}/stages/`);
          const stageData = await stageResp.json();
          const stages = stageData.data || [];
          const prodStage = stages.find(s => s.name === 'prod') || stages[0];

          if (!prodStage) return { error: 'No stage found' };

          // Publish
          const resp = await fetch(`/backend/gateways/${gwId}/releases/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
              stage_id: prodStage.id,
              resource_version_id: versnId,
              comment: 'BDD test publish',
            }),
          });
          const data = await resp.json();
          return { ok: resp.ok, status: resp.status, data };
        } catch(e) {
          return { error: e.message };
        }
      }, { gwId: gatewayId, versnId: versionId });

      console.log(`[setup] Resource version published: ${JSON.stringify(publishResult).substring(0, 200)}`);
    }

    console.log('[setup] Resource version generated and published');

    // === Save state for tests ===
    // Set env vars directly so Playwright workers inherit them
    process.env.TEST_GATEWAY_ID = gatewayId;
    process.env.TEST_GATEWAY_NAME = testName;

    const storageState = await context.storageState();
    fs.writeFileSync(
      ENV_FILE,
      `TEST_GATEWAY_ID=${gatewayId}\nTEST_GATEWAY_NAME=${testName}\n`
    );

    // Save storage state for test reuse
    fs.writeFileSync(
      path.join(__dirname, 'storage-state.json'),
      JSON.stringify(storageState)
    );

    console.log(`[setup] Complete. Gateway: ${testName} (ID: ${gatewayId})`);
  } finally {
    await browser.close();
  }
};
