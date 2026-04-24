// test-bdd/scripts/helpers.js
// Shared utility functions for BDD test scripts

const fs = require('fs');
const path = require('path');
const { BASE_URL, USERNAME, PASSWORD, COOKIE } = require('./test-env');

/**
 * Lazily read TEST_GATEWAY_ID from the .env file written by globalSetup.
 * Must be called at test runtime (inside test/beforeEach), NOT at module top level,
 * because globalSetup hasn't run yet when modules are first evaluated.
 */
function getGatewayId() {
  // Check process.env first (may be set by globalSetup in same process)
  if (process.env.TEST_GATEWAY_ID) return process.env.TEST_GATEWAY_ID;

  // Read from .env file written by setup.js
  const envFile = path.join(__dirname, '.env');
  if (fs.existsSync(envFile)) {
    const content = fs.readFileSync(envFile, 'utf-8');
    const match = content.match(/TEST_GATEWAY_ID=(\d+)/);
    if (match) {
      process.env.TEST_GATEWAY_ID = match[1]; // cache for subsequent calls
      return match[1];
    }
  }
  throw new Error('TEST_GATEWAY_ID not available — globalSetup may have failed');
}

/**
 * Full login flow using environment credentials.
 * Handles both Chinese and English login forms.
 */
async function login(page) {
  await page.goto(BASE_URL);
  await page.waitForTimeout(3000);

  const url = page.url();
  if (!url.includes('/login/')) {
    return; // already logged in
  }

  if (COOKIE) {
    const domain = new URL(BASE_URL).hostname.split('.').slice(-2).join('.');
    await page.context().addCookies([
      { name: 'bk_token', value: COOKIE, domain: '.' + domain, path: '/' },
    ]);
    await page.goto(BASE_URL);
    await page.waitForTimeout(3000);
    return;
  }

  // Chinese form detection
  const hasChineseForm = await page.locator('input[placeholder="请输入用户名"]').isVisible().catch(() => false);

  if (hasChineseForm) {
    await page.locator('input[placeholder="请输入用户名"]').click();
    await page.locator('input[placeholder="请输入用户名"]').type(USERNAME);
    await page.locator('input[placeholder="请输入密码"]').click();
    await page.locator('input[placeholder="请输入密码"]').type(PASSWORD);
    await page.locator('button').filter({ hasText: '立即登录' }).click();
  } else {
    // English form fallback
    const hasIdUser = await page.locator('#user').isVisible().catch(() => false);
    if (hasIdUser) {
      await page.locator('#user').click();
      await page.locator('#user').type(USERNAME);
      await page.locator('#password').click();
      await page.locator('#password').type(PASSWORD);
      await page.locator('.login-btn').click();
    } else {
      await page.getByRole('textbox', { name: /username/i }).fill(USERNAME);
      await page.getByRole('textbox', { name: /password/i }).fill(PASSWORD);
      await page.getByRole('button', { name: /log in/i }).click();
    }
  }

  // Wait for redirect away from login
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(500);
    if (!page.url().includes('/login/')) break;
  }

  if (page.url().includes('/login/')) {
    throw new Error('Login failed — still on login page after 15 seconds');
  }
}

/**
 * Re-authenticate when session expires mid-test.
 */
async function reAuth(page) {
  const currentUrl = page.url();
  await login(page);
  if (currentUrl && !currentUrl.includes('/login/')) {
    await page.goto(currentUrl);
    await page.waitForTimeout(2000);
  }
}

/**
 * Wait for page to be fully ready (network idle + main content visible).
 */
async function waitForPageReady(page) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(800);
}

/**
 * Known parent-menu → sub-menu mappings for collapsed sidebar groups.
 * When a target menuText is a sub-item, we must first expand its parent group.
 */
const SUB_MENU_PARENTS = {
  '权限审批': '权限管理',
  '应用权限': '权限管理',
  '流水日志': '运行数据',
  '统计报表': '运行数据',
  '发布记录': '发布',
  '操作记录': '审计信息',
  'MCP权限审批': '权限管理',
};

/**
 * Navigate to a gateway sub-page by first loading the overview (to initialize Vue SPA context),
 * then navigating to the target page. The SPA requires the overview to be loaded first for
 * many pages — direct URL navigation often results in empty content.
 *
 * Strategy: Load overview → wait for sidebar → navigate via sidebar click or direct URL.
 *
 * @param {Page} page - Playwright page
 * @param {string} gatewayId - Gateway ID (e.g., process.env.TEST_GATEWAY_ID)
 * @param {string} menuText - Sidebar menu item text (e.g., '资源配置', '后端服务')
 * @param {string} [fallbackPath] - Direct URL path as fallback (e.g., '/resource/setting')
 */
async function navigateToGatewayPage(page, gatewayId, menuText, fallbackPath) {
  const baseUrl = BASE_URL.replace(/\/$/, '');
  const overviewUrl = `${baseUrl}/${gatewayId}/stage/overview`;

  // Step 1: Load gateway overview to initialize SPA context.
  // Retry up to 3 times if sidebar doesn't appear.
  let sidebarVisible = false;
  for (let attempt = 0; attempt < 3; attempt++) {
    await page.goto(overviewUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(2000);

    // Handle auth redirect
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await page.goto(overviewUrl, { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle').catch(() => {});
      await page.waitForTimeout(2000);
    }

    // Wait for sidebar to appear — check for gateway selector or menu items
    sidebarVisible = await page.locator('textbox[value], .bk-menu-item, [class*="menu-item"]').first()
      .waitFor({ timeout: 10000 })
      .then(() => true)
      .catch(() => false);

    if (sidebarVisible) break;
  }

  if (!sidebarVisible && fallbackPath) {
    // Last resort: try direct navigation
    await page.goto(`${baseUrl}/${gatewayId}${fallbackPath}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(2000);
    return;
  }

  // Step 2: Navigate to target page
  if (fallbackPath) {
    // Use direct URL navigation after SPA is initialized — more reliable than sidebar clicks
    await page.goto(`${baseUrl}/${gatewayId}${fallbackPath}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(2000);
  } else {
    // No fallbackPath — use sidebar navigation
    const parentMenu = SUB_MENU_PARENTS[menuText];
    if (parentMenu) {
      const parentItem = page.locator('.bk-menu-item, .bk-submenu, [class*="submenu"], [class*="menu-group"]').filter({ hasText: parentMenu }).first();
      if (await parentItem.isVisible({ timeout: 3000 }).catch(() => false)) {
        await parentItem.click();
        await page.waitForTimeout(800);
      }
    }

    const menuItem = page.locator('.bk-menu-item').filter({ hasText: menuText }).first();
    if (await menuItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await menuItem.click();
      await page.waitForTimeout(3000);
    }
  }
}

/**
 * Fill multiple form fields.
 * @param {Object} fields - { selector: value, ... } or [{ selector, value }, ...]
 */
async function fillForm(page, fields) {
  const entries = Array.isArray(fields) ? fields : Object.entries(fields).map(([s, v]) => ({ selector: s, value: v }));
  for (const { selector, value } of entries) {
    const el = page.locator(selector).first();
    await el.click();
    await el.fill(value);
    await page.waitForTimeout(200);
  }
}

/**
 * Select an option from a BkSelect dropdown.
 * NEVER uses Escape — uses body click to dismiss.
 */
async function selectDropdown(page, selector, optionText) {
  // Dismiss any open dropdown first
  await page.locator('body').click({ position: { x: 10, y: 10 } });
  await page.waitForTimeout(200);

  // Open the target dropdown
  await page.locator(selector).first().click({ force: true });
  await page.waitForTimeout(300);

  // Select the option
  await page.locator('.bk-select-option, .bk-option').filter({ hasText: optionText }).first().click();
  await page.waitForTimeout(800);
}

/**
 * Close a sideslider, handling confirmation dialogs if present.
 */
async function closeSlider(page) {
  const closeBtn = page.locator('.bk-sideslider .bk-sideslider-closer, .bk-sideslider-closer');
  if (await closeBtn.isVisible().catch(() => false)) {
    await closeBtn.click({ force: true });
    await page.waitForTimeout(500);

    // Handle confirmation dialog
    const confirmBtn = page.locator('.bk-dialog .bk-dialog-footer button').filter({ hasText: /确定|确认/ }).first();
    if (await confirmBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await confirmBtn.click({ force: true });
      await page.waitForTimeout(500);
    }
  }
}

/**
 * Get toast notification message text.
 */
async function getToastMessage(page) {
  const toast = page.locator('.bk-message, .bk-notify, [class*="toast"], [class*="message"]').first();
  await toast.waitFor({ timeout: 5000 }).catch(() => {});
  return await toast.textContent().catch(() => '');
}

/**
 * Count visible table rows (excluding header).
 */
async function getTableRowCount(page) {
  await page.waitForTimeout(500);
  return await page.locator('table tbody tr, .bk-table-body tr, .table-row').count();
}

/**
 * Check if the page has redirected to login (session expired).
 */
function isSessionExpired(page) {
  return page.url().includes('/login/');
}

module.exports = {
  login,
  reAuth,
  waitForPageReady,
  navigateToGatewayPage,
  fillForm,
  selectDropdown,
  closeSlider,
  getToastMessage,
  getTableRowCount,
  isSessionExpired,
  getGatewayId,
  BASE_URL,
};
