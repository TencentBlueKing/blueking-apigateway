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

    // === Step 3: Configure backend service ===
    await page.goto(`${BASE_URL}/${gatewayId}/backends`);
    await page.waitForTimeout(2000);

    // Edit the default backend service
    const editBtn = page.locator('button, a').filter({ hasText: /编辑/ }).first();
    if (await editBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await editBtn.click({ force: true });
      await page.waitForTimeout(1500);

      // Fill backend address
      const addrInput = page.locator('input[placeholder*="地址"], input[placeholder*="host"]').first();
      if (await addrInput.isVisible().catch(() => false)) {
        await addrInput.fill('httpbin.org:80');
        await page.waitForTimeout(300);
      }

      // Confirm
      const confirmBtn = page.locator('button').filter({ hasText: /确定|保存/ }).first();
      if (await confirmBtn.isVisible().catch(() => false)) {
        await confirmBtn.click({ force: true });
        await page.waitForTimeout(2000);
      }
    }

    console.log('[setup] Backend service configured');

    // === Step 4: Create a test resource ===
    await page.goto(`${BASE_URL}/${gatewayId}/resource/create`);
    await page.waitForTimeout(2000);

    // Fill resource name
    const resNameInput = page.locator('input[placeholder*="资源名称"], input[name*="name"]').first();
    if (await resNameInput.isVisible().catch(() => false)) {
      const resName = 'test_resource_' + Date.now().toString().slice(-4);
      await resNameInput.fill(resName);
      await page.waitForTimeout(300);

      // Fill request path
      const pathInput = page.locator('input[placeholder*="请求路径"], input[placeholder*="/"]').first();
      if (await pathInput.isVisible().catch(() => false)) {
        await pathInput.fill('/test/' + resName);
        await page.waitForTimeout(300);
      }

      // Fill backend path
      const backendPath = page.locator('input[placeholder*="后端"]').first();
      if (await backendPath.isVisible().catch(() => false)) {
        await backendPath.fill('/get');
        await page.waitForTimeout(300);
      }

      // Submit
      await page.locator('button').filter({ hasText: '提交' }).click({ force: true });
      await page.waitForTimeout(3000);
    }

    console.log('[setup] Test resource created');

    // === Step 5: Generate resource version ===
    await page.goto(`${BASE_URL}/${gatewayId}/resource/setting`);
    await page.waitForTimeout(2000);

    const genBtn = page.locator('button').filter({ hasText: '生成版本' }).first();
    if (await genBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await genBtn.click({ force: true });
      await page.waitForTimeout(2000);

      // Step 1: diff confirmation → 下一步
      const nextBtn = page.locator('button').filter({ hasText: '下一步' }).first();
      if (await nextBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nextBtn.click({ force: true });
        await page.waitForTimeout(2000);
      }

      // Step 2: confirm → 确定
      const okBtn = page.locator('.bk-sideslider button').filter({ hasText: '确定' }).first();
      if (await okBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await okBtn.click({ force: true });
        await page.waitForTimeout(5000);
      }

      // Click 立即发布 if visible
      const publishNow = page.locator('button').filter({ hasText: '立即发布' }).first();
      if (await publishNow.isVisible({ timeout: 5000 }).catch(() => false)) {
        await publishNow.click({ force: true });
        await page.waitForTimeout(2000);

        // Select prod stage
        const stageSelect = page.locator('.bk-select').first();
        if (await stageSelect.isVisible().catch(() => false)) {
          await stageSelect.click({ force: true });
          await page.waitForTimeout(300);
          await page.locator('.bk-select-option').filter({ hasText: 'prod' }).click();
          await page.waitForTimeout(1000);
        }

        // 下一步
        const nextBtn2 = page.locator('button').filter({ hasText: '下一步' }).first();
        if (await nextBtn2.isVisible({ timeout: 2000 }).catch(() => false)) {
          await nextBtn2.click({ force: true });
          await page.waitForTimeout(2000);
        }

        // 确认发布
        const confirmPublish = page.locator('button').filter({ hasText: '确认发布' }).first();
        if (await confirmPublish.isVisible({ timeout: 3000 }).catch(() => false)) {
          await confirmPublish.click({ force: true });
          await page.waitForTimeout(1000);
        }

        // InfoBox confirmation
        const infoConfirm = page.locator('.bk-infobox button').filter({ hasText: /确认|确定/ }).first();
        if (await infoConfirm.isVisible({ timeout: 3000 }).catch(() => false)) {
          await infoConfirm.click({ force: true });
          await page.waitForTimeout(5000);
        }
      }
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
