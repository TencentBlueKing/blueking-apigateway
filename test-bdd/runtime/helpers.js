// test-bdd/scripts/helpers.js
// Shared utility functions for BDD test scripts

const fs = require('fs');
const path = require('path');
const { BASE_URL, USERNAME, PASSWORD, COOKIE } = require('./test-env');

const RUNTIME_ENV_FILE = path.join(__dirname, '.env');
const STORAGE_STATE_FILE = path.join(__dirname, 'storage-state.json');
const TABLE_ROW_SELECTOR = 'table tbody tr, .bk-table-body tr, .table-row';
const GATEWAY_LIST_SELECTOR = '.table-list .table-item, .table-item, .gateway-card, .gateway-item, table tbody tr, [class*="gateway-card"]';
const PLUGIN_BINDING_SELECTOR = '.binding-plugins .bk-collapse-item, .binding-plugins .bk-collapse-panel, .binding-plugins [class*="collapse-item"]';
const PLUGIN_SELECTION_SELECTOR = '.plugin-list .plugin';

function readRuntimeState() {
  if (!fs.existsSync(RUNTIME_ENV_FILE)) {
    return {};
  }

  return fs.readFileSync(RUNTIME_ENV_FILE, 'utf-8')
    .split(/\r?\n/)
    .filter(Boolean)
    .reduce((state, line) => {
      const separatorIndex = line.indexOf('=');
      if (separatorIndex <= 0) {
        return state;
      }

      const key = line.slice(0, separatorIndex);
      const value = line.slice(separatorIndex + 1);
      state[key] = value;
      return state;
    }, {});
}

function writeRuntimeState(values) {
  const nextState = {
    ...readRuntimeState(),
  };

  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === null) {
      continue;
    }
    nextState[key] = String(value);
  }

  const content = Object.entries(nextState)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');
  fs.writeFileSync(RUNTIME_ENV_FILE, content ? `${content}\n` : '');
  return nextState;
}

function cleanupRuntimeArtifacts(files = [RUNTIME_ENV_FILE, STORAGE_STATE_FILE]) {
  for (const file of files) {
    try {
      fs.unlinkSync(file);
    } catch {
      // Best-effort cleanup.
    }
  }
}

function sanitizeTestName(value) {
  return String(value || 'test')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-+|-+$/g, '');
}

function createTestName(prefix, options = {}) {
  const {
    maxLength = 30,
    suffixLength = 6,
  } = options;

  const safePrefix = sanitizeTestName(prefix) || 'test';
  const token = Date.now().toString(36).slice(-suffixLength);
  const separator = safePrefix.endsWith('-') ? '' : '-';
  const prefixBudget = Math.max(0, maxLength - separator.length - token.length);
  const trimmedPrefix = safePrefix.slice(0, prefixBudget).replace(/-+$/g, '');

  if (!trimmedPrefix) {
    return token.slice(0, maxLength);
  }

  return `${trimmedPrefix}${separator}${token}`;
}

function createTestIdentifier(prefix, options = {}) {
  const {
    maxLength = 30,
    suffixLength = 6,
  } = options;

  const safePrefix = String(prefix || 'bdd')
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/_{2,}/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/^[^a-z]+/, 'bdd_') || 'bdd';
  const token = Date.now().toString(36).slice(-suffixLength).replace(/[^a-z0-9]/g, '');
  const separator = safePrefix.endsWith('_') ? '' : '_';
  const prefixBudget = Math.max(1, maxLength - separator.length - token.length);
  const trimmedPrefix = safePrefix.slice(0, prefixBudget).replace(/_+$/g, '') || 'bdd';
  return `${trimmedPrefix}${separator}${token}`.slice(0, maxLength).replace(/_+$/g, '');
}

/**
 * Lazily read TEST_GATEWAY_ID from the .env file written by globalSetup.
 * Must be called at test runtime (inside test/beforeEach), NOT at module top level,
 * because globalSetup hasn't run yet when modules are first evaluated.
 */
function getGatewayId() {
  // Check process.env first (may be set by globalSetup in same process)
  if (process.env.TEST_GATEWAY_ID) return process.env.TEST_GATEWAY_ID;

  const runtimeState = readRuntimeState();
  if (runtimeState.TEST_GATEWAY_ID) {
    process.env.TEST_GATEWAY_ID = runtimeState.TEST_GATEWAY_ID;
    return runtimeState.TEST_GATEWAY_ID;
  }

  throw new Error('TEST_GATEWAY_ID not available — globalSetup may have failed');
}

function extractCsrfTokenFromCookieString(cookieString) {
  const match = String(cookieString || '').match(
    /(?:bkapigw_csrftoken_[^=]*|bk_apigw_dashboard_csrftoken|bk_csrftoken|csrftoken)=([^;]+)/
  );
  return match ? match[1] : '';
}

async function getCsrfToken(page) {
  return await page.evaluate(() => {
    const match = document.cookie.match(
      /(?:bkapigw_csrftoken_[^=]*|bk_apigw_dashboard_csrftoken|bk_csrftoken|csrftoken)=([^;]+)/
    );
    return match ? match[1] : '';
  }).catch(() => '');
}

async function hasAuthenticatedSession(page) {
  return await page.evaluate(async () => {
    try {
      const resp = await fetch('/backend/accounts/userinfo/', { credentials: 'include' });
      const match = document.cookie.match(
        /(?:bkapigw_csrftoken_[^=]*|bk_apigw_dashboard_csrftoken|bk_csrftoken|csrftoken)=([^;]+)/
      );
      return resp.ok && Boolean(match);
    } catch {
      return false;
    }
  }).catch(() => false);
}

async function waitForAuthenticatedSession(page, timeout = 15000) {
  const deadline = Date.now() + timeout;

  while (Date.now() < deadline) {
    if (await hasAuthenticatedSession(page)) {
      return true;
    }
    await page.waitForTimeout(500);
  }

  return false;
}

async function dismissLoginOverlays(page) {
  const noticeButton = page.locator('button, .bk-button').filter({ hasText: /I know|我知道|知道了/ }).first();
  if (await noticeButton.isVisible({ timeout: 1000 }).catch(() => false)) {
    await noticeButton.evaluate((button) => button.click()).catch(() => {});
    await page.waitForTimeout(300);
  }
}

async function waitForLoginSurface(page, timeout = 30000) {
  const deadline = Date.now() + timeout;

  while (Date.now() < deadline) {
    await dismissLoginOverlays(page);

    if (await hasAuthenticatedSession(page)) {
      return 'authenticated';
    }

    if (await page.locator('input[placeholder="请输入用户名"]').isVisible({ timeout: 500 }).catch(() => false)) {
      return 'chinese';
    }

    if (await page.locator('#user').isVisible({ timeout: 500 }).catch(() => false)) {
      return 'id';
    }

    const englishUsername = page.locator(
      'input[placeholder="Please enter your username"], input[name="username"], input[type="text"]'
    ).first();
    const englishPassword = page.locator(
      'input[placeholder="Please enter your password"], input[name="password"], input[type="password"]'
    ).first();
    if (
      await englishUsername.isVisible({ timeout: 500 }).catch(() => false)
      && await englishPassword.isVisible({ timeout: 500 }).catch(() => false)
    ) {
      return 'english';
    }

    if (await isTransientUnavailablePage(page)) {
      await page.waitForTimeout(2000);
      await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' }).catch(() => {});
      await page.waitForLoadState('networkidle').catch(() => {});
      continue;
    }

    await page.waitForTimeout(1000);
  }

  return 'unknown';
}

/**
 * Full login flow using environment credentials.
 * Handles both Chinese and English login forms.
 */
async function login(page) {
  await gotoWithTransientWait(page, BASE_URL);
  await dismissLoginOverlays(page);

  const loginState = await waitForLoginSurface(page, 30000);
  const url = page.url();
  if (loginState === 'authenticated' || !url.includes('/login/') && await waitForAuthenticatedSession(page, 5000)) {
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

  if (loginState === 'chinese') {
    await page.locator('input[placeholder="请输入用户名"], #user').first().fill(USERNAME);
    await page.locator('input[placeholder="请输入密码"], #password').first().fill(PASSWORD);
    await page.locator('button').filter({ hasText: '立即登录' }).evaluate((button) => button.click());
  } else if (loginState === 'id') {
    await page.locator('#user').fill(USERNAME);
    await page.locator('#password').fill(PASSWORD);
    await page.locator('.login-btn, button').filter({ hasText: /立即登录|Log in/i }).first().evaluate((button) => button.click());
  } else if (loginState === 'english') {
    await page.locator('input[placeholder="Please enter your username"], input[name="username"], input[type="text"]').first().fill(USERNAME);
    await page.locator('input[placeholder="Please enter your password"], input[name="password"], input[type="password"]').first().fill(PASSWORD);
    await page.getByRole('button', { name: /log in/i }).evaluate((button) => button.click());
  } else {
    const bodyText = await page.locator('body').textContent({ timeout: 1000 }).catch(() => '');
    throw new Error(`Login form not ready after waiting: ${bodyText.slice(0, 120)}`);
  }

  // Wait for redirect away from login
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(500);
    await dismissLoginOverlays(page);
    if (!page.url().includes('/login/')) break;
  }

  const sessionReady = await waitForAuthenticatedSession(page, 15000);

  if (page.url().includes('/login/') || !sessionReady) {
    throw new Error('Login failed — dashboard session or CSRF cookie not ready');
  }

  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(1000);
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

const FATAL_PAGE_TEXT_PATTERN = /(?:^|\b)(?:500|502|503|504)(?:\b|$)|Server Error|Internal Server Error|OperationalError|Traceback|Bad Gateway|Service(?: Temporarily)? Unavailable|Gateway Timeout|系统出现异常|努力恢复中|请稍后再试|页面找不到|404页|404 page|page not found/i;
const FATAL_EXCEPTION_TEXT_PATTERN = /500|502|503|504|Server Error|Internal Server Error|OperationalError|Traceback|Bad Gateway|Service(?: Temporarily)? Unavailable|Gateway Timeout|系统出现异常|努力恢复中|请稍后再试|页面找不到|404页|404 page|page not found/i;
const IGNORED_FAILURE_URL_PATTERN = /(?:sockjs-node|webpack|vite|hot-update|favicon\.ico|\.map(?:\?|$))/i;
const NON_FATAL_PAGE_ERROR_PATTERN = /请求方法\+请求路径在网关下唯一|请至少调整其中一项/i;

function isFatalNetworkResponse(response) {
  const url = response.url();
  if (IGNORED_FAILURE_URL_PATTERN.test(url)) return false;

  const status = response.status();
  if (status >= 500) return true;

  // The production gate treats application 404 pages as broken routes. Ignore static 404s.
  if (status === 404 && /\/backend\/|\/api\/|\/gateways\/|\/components\/|\/docs\/|\/mcp-|\/platform-tools|\/personal-workbench|\/monitor\//.test(url)) {
    return true;
  }

  return false;
}

function attachHardFailureGuard(page, options = {}) {
  if (page.__bddHardFailureGuardAttached) {
    return page.__bddHardFailureState;
  }

  const state = {
    failures: [],
    options,
  };
  page.__bddHardFailureGuardAttached = true;
  page.__bddHardFailureState = state;

  page.on('pageerror', (error) => {
    if (NON_FATAL_PAGE_ERROR_PATTERN.test(error.message || '')) return;
    state.failures.push(`pageerror: ${error.message}`);
  });

  page.on('requestfailed', (request) => {
    const url = request.url();
    const resourceType = request.resourceType();
    const failure = request.failure();
    const errorText = failure ? failure.errorText : '';
    if (IGNORED_FAILURE_URL_PATTERN.test(url)) return;
    if (!['document', 'xhr', 'fetch'].includes(resourceType)) return;
    if (/net::ERR_ABORTED/i.test(errorText)) return;
    state.failures.push(`request failed: ${request.method()} ${url} ${errorText}`.trim());
  });

  page.on('response', (response) => {
    if (!isFatalNetworkResponse(response)) return;
    state.failures.push(`fatal response: ${response.status()} ${response.url()}`);
  });

  return state;
}

function clearHardFailureGuard(page) {
  if (page.__bddHardFailureState) {
    page.__bddHardFailureState.failures = [];
  }
}

async function getFatalPageText(page) {
  const bodyText = await page.locator('body').textContent({ timeout: 1000 }).catch(() => '');
  if (FATAL_PAGE_TEXT_PATTERN.test(bodyText || '')) {
    return (bodyText || '').replace(/\s+/g, ' ').trim().slice(0, 500);
  }

  const exceptionTexts = await page.locator('.bk-exception, [class*="exception"], [class*="error-page"], [class*="fail-page"]').evaluateAll((nodes) => (
    nodes.map(node => node.textContent || '').filter(Boolean)
  )).catch(() => []);

  const fatalException = exceptionTexts.find(text => FATAL_EXCEPTION_TEXT_PATTERN.test(text));
  if (fatalException) {
    return fatalException.replace(/\s+/g, ' ').trim().slice(0, 500);
  }

  return '';
}

async function assertNoHardFailure(page, context = '') {
  attachHardFailureGuard(page);

  const state = page.__bddHardFailureState || { failures: [] };
  const fatalPageText = await getFatalPageText(page);
  if (fatalPageText) {
    state.failures.push(`fatal page content${context ? ` after ${context}` : ''}: ${fatalPageText}`);
  }

  if (state.failures.length > 0) {
    const details = state.failures.slice(0, 10).join('\n');
    throw new Error(`BDD hard failure guard detected ${state.failures.length} fatal issue(s)${context ? ` (${context})` : ''}:\n${details}`);
  }
}

async function waitForPageReadyAndAssert(page, context = 'page ready') {
  await waitForPageReady(page);
  await assertNoHardFailure(page, context);
}

async function waitForGatewayHomeReady(page) {
  await page.goto(`${BASE_URL}/`);
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(3000);
  if (page.url().includes('/login/')) {
    await reAuth(page);
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);
  }

  await page.locator(`${GATEWAY_LIST_SELECTOR}, .bk-exception`).first().waitFor({ timeout: 15000 }).catch(() => {});
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

async function isTransientUnavailablePage(page) {
  const bodyText = await page.locator('body').textContent({ timeout: 1000 }).catch(() => '');
  return /OperationalError|Can't connect to MySQL server|Name or service not known|Bad Gateway|Service(?: Temporarily)? Unavailable|Gateway Timeout|503|系统出现异常|努力恢复中|请稍后再试/i
    .test(bodyText || '');
}

async function gotoWithTransientWait(page, url, options = {}) {
  const attempts = options.attempts || 5;
  let lastNavigationError = null;
  let lastStatus = 0;

  for (let attempt = 1; attempt <= attempts; attempt++) {
    lastNavigationError = null;
    lastStatus = 0;
    const response = await page.goto(url, { waitUntil: 'domcontentloaded' }).catch((error) => {
      lastNavigationError = error;
      return null;
    });
    await page.waitForLoadState('networkidle').catch(() => {});

    lastStatus = response ? response.status() : 0;
    const transientUnavailable = lastNavigationError
      || lastStatus >= 500
      || await isTransientUnavailablePage(page);

    if (!transientUnavailable) {
      await page.waitForTimeout(1000);
      await assertNoHardFailure(page, `navigate to ${url}`);
      return;
    }

    if (attempt < attempts) {
      await page.waitForTimeout(Math.min(15000, 3000 * attempt));
    }
  }

  throw new Error(
    `Dashboard page stayed unavailable after ${attempts} attempts: ${url}`
    + (lastStatus ? ` (last status: ${lastStatus})` : '')
    + (lastNavigationError ? ` (${lastNavigationError.message})` : '')
  );
}

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
  // Retry while the shared dev dashboard is publishing or temporarily unavailable.
  let sidebarVisible = false;
  for (let attempt = 0; attempt < 5; attempt++) {
    await gotoWithTransientWait(page, overviewUrl);

    // Handle auth redirect
    if (page.url().includes('/login/')) {
      await reAuth(page);
      await gotoWithTransientWait(page, overviewUrl);
    }

    // Wait for sidebar to appear — check for gateway selector or menu items
    sidebarVisible = await page.locator('textbox[value], .bk-menu-item, [class*="menu-item"]').first()
      .waitFor({ timeout: 10000 })
      .then(() => true)
      .catch(() => false);

    if (sidebarVisible) break;
    await page.waitForTimeout(3000);
  }

  if (!sidebarVisible && fallbackPath) {
    // Last resort: try direct navigation
    await gotoWithTransientWait(page, `${baseUrl}/${gatewayId}${fallbackPath}`);
    await assertNoHardFailure(page, `${gatewayId}${fallbackPath}`);
    return;
  }

  // Step 2: Navigate to target page
  if (fallbackPath) {
    // Use direct URL navigation after SPA is initialized — more reliable than sidebar clicks
    await gotoWithTransientWait(page, `${baseUrl}/${gatewayId}${fallbackPath}`);
    await assertNoHardFailure(page, `${gatewayId}${fallbackPath}`);
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

async function openStageOverviewTab(page, tabText) {
  const detailTab = page.locator('button, .bk-tab, [class*="tab"], [class*="mode"]').filter({ hasText: /详情|列表/ }).first();
  if (await detailTab.isVisible({ timeout: 3000 }).catch(() => false)) {
    await detailTab.click();
    await page.waitForTimeout(800);
  }

  const stageSelect = page.locator('.bk-select, .stage-select').first();
  if (await stageSelect.isVisible().catch(() => false)) {
    await stageSelect.click();
    await page.waitForTimeout(300);
    const firstStageOption = page.locator('.bk-select-option, .bk-option').first();
    if (await firstStageOption.isVisible({ timeout: 3000 }).catch(() => false)) {
      await firstStageOption.click();
      await page.waitForTimeout(300);
    }
    await dismissFloatingLayers(page);
  }

  const targetTab = page.locator('.bk-tab, [class*="tab"], a, button').filter({ hasText: tabText }).first();
  if (await targetTab.isVisible().catch(() => false)) {
    await targetTab.click();
    await page.waitForTimeout(800);
  }
}

async function navigateToStageOverviewTab(page, gatewayId, tabText) {
  await navigateToGatewayPage(page, gatewayId, '环境概览', '/stage/overview');
  await openStageOverviewTab(page, tabText);
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
  await selectDropdownOption(page, selector, optionText);
  await page.waitForTimeout(500);
}

async function dismissFloatingLayers(page) {
  await page.locator('body').click({ position: { x: 10, y: 10 } }).catch(() => {});
  await page.waitForTimeout(200);
}

async function selectDropdownOption(page, trigger, optionText = null, optionSelector = '.bk-select-option, .bk-option') {
  const triggerLocator = typeof trigger === 'string'
    ? page.locator(trigger).first()
    : trigger.first();

  await dismissFloatingLayers(page);

  if (!await triggerLocator.isVisible({ timeout: 3000 }).catch(() => false)) {
    return false;
  }

  await triggerLocator.click({ force: true });
  await page.waitForTimeout(300);

  const options = page.locator(optionSelector);
  const option = optionText
    ? options.filter({ hasText: optionText }).first()
    : options.first();

  if (!await option.isVisible({ timeout: 3000 }).catch(() => false)) {
    await dismissFloatingLayers(page);
    return false;
  }

  await option.click({ force: true });
  await page.waitForTimeout(300);
  await dismissFloatingLayers(page);
  return true;
}

async function getActiveOverlay(page) {
  const sideslider = getActiveSideslider(page);
  if (await sideslider.isVisible({ timeout: 1000 }).catch(() => false)) {
    return sideslider;
  }

  return getActiveDialog(page);
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

function getVisibleTableRows(page, selector = TABLE_ROW_SELECTOR) {
  return page.locator(selector).filter({ hasNotText: '暂无数据' });
}

function getGatewayListItems(page) {
  return page.locator(GATEWAY_LIST_SELECTOR);
}

function getGatewayListItemByText(page, text) {
  return getGatewayListItems(page).filter({ hasText: text }).first();
}

function getFirstVisibleTableRow(page, selector = TABLE_ROW_SELECTOR) {
  return getVisibleTableRows(page, selector).first();
}

function getTableRowByText(page, text, selector = TABLE_ROW_SELECTOR) {
  return getVisibleTableRows(page, selector).filter({ hasText: text }).first();
}

function getTableRowActionButton(row, textPattern, selector = 'button, a, .bk-button') {
  return row.locator(selector).filter({ hasText: textPattern }).first();
}

async function selectVisibleTableRowCheckboxes(page, limit = 1, selector = TABLE_ROW_SELECTOR) {
  return await page.evaluate(({ rowSelector, maxCount }) => {
    const rows = document.querySelectorAll(rowSelector);
    let clickCount = 0;

    for (const row of rows) {
      if (row.textContent.includes('暂无数据')) continue;

      const checkbox = row.querySelector('.bk-checkbox-input, label.bk-checkbox, .bk-checkbox-original');
      if (!checkbox) continue;

      checkbox.click();
      clickCount++;
      if (clickCount >= maxCount) break;
    }

    return clickCount;
  }, { rowSelector: selector, maxCount: limit });
}

function getActiveSideslider(page) {
  return page.locator('.bk-sideslider:visible').last();
}

function getActiveDialog(page) {
  return page.locator('.bk-dialog:visible, .bk-infobox:visible, .bk-modal-wrapper:visible, .bk-modal:visible, [role="dialog"]:visible').last();
}

function getActionButton(scope, textPattern, selector = 'button, a, .bk-button') {
  return scope.locator(selector).filter({ hasText: textPattern }).first();
}

function getFirstResourcePluginCountLink(page) {
  return getVisibleTableRows(page).first()
    .locator('a, .link, [class*="link"]').filter({ hasText: /^\d+$/ }).first();
}

async function openFirstResourcePluginPanel(page) {
  const pluginCount = getFirstResourcePluginCountLink(page);
  if (await pluginCount.isVisible({ timeout: 5000 }).catch(() => false)) {
    await pluginCount.click();
    await page.waitForTimeout(800);
    return true;
  }
  return false;
}

function getPluginBindingItems(page) {
  return page.locator(PLUGIN_BINDING_SELECTOR);
}

function getPluginBindingItemByText(page, text) {
  return getPluginBindingItems(page).filter({ hasText: text }).first();
}

function getPluginSelectionOptions(page) {
  return page.locator(PLUGIN_SELECTION_SELECTOR);
}

function getPluginSelectionOptionByText(page, text) {
  return getPluginSelectionOptions(page).filter({ hasText: text }).first();
}

function getAvailablePluginSelectionOption(page, preferredText = null) {
  const options = getPluginSelectionOptions(page);
  if (preferredText) {
    return options.filter({ hasText: preferredText, hasNotText: '已添加' }).first();
  }
  return options.filter({ hasNotText: '已添加' }).first();
}

async function clickConfirm(page, textPattern = /确定|确认/, scope = null) {
  const actionScope = scope || getActiveDialog(page);
  const confirmBtn = getActionButton(actionScope, textPattern);

  if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await confirmBtn.click({ force: true });
    await page.waitForTimeout(500);
    return true;
  }

  return false;
}

/**
 * Count visible table rows (excluding header).
 */
async function getTableRowCount(page) {
  await page.waitForTimeout(500);
  return await getVisibleTableRows(page).count();
}

/**
 * Check if the page has redirected to login (session expired).
 */
function isSessionExpired(page) {
  return page.url().includes('/login/');
}

function normalizeApiPath(requestPath) {
  if (/^https?:\/\//.test(requestPath)) {
    return requestPath;
  }

  const pathWithSlash = requestPath.startsWith('/') ? requestPath : `/${requestPath}`;
  return pathWithSlash.startsWith('/backend/') ? pathWithSlash : `/backend${pathWithSlash}`;
}

async function apiRequest(page, method, requestPath, data = undefined, options = {}) {
  const csrfToken = await getCsrfToken(page);
  const maxAttempts = options.retryHtml500 === false ? 1 : 6;
  let response;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    response = await page.evaluate(async ({ method: requestMethod, requestPath: rawPath, data: payload, options: requestOptions, csrf }) => {
      const url = new URL(rawPath, window.location.origin);
      const headers = { Accept: 'application/json' };
      const init = {
        method: requestMethod,
        credentials: 'include',
        headers,
      };

      if (csrf) {
        headers['X-CSRFToken'] = csrf;
      }

      if (payload !== undefined && payload !== null) {
        if (requestMethod === 'GET' || requestOptions.query === true) {
          for (const [key, value] of Object.entries(payload)) {
            if (value === undefined || value === null) continue;
            if (Array.isArray(value)) {
              value.forEach(item => url.searchParams.append(key, String(item)));
            } else {
              url.searchParams.set(key, String(value));
            }
          }
        } else {
          headers['Content-Type'] = 'application/json';
          init.body = JSON.stringify(payload);
        }
      }

      const resp = await fetch(url.toString(), init);
      const contentType = resp.headers.get('content-type') || '';
      let body;

      if (requestOptions.responseType === 'blob') {
        const blob = await resp.blob();
        body = { size: blob.size, type: blob.type };
      } else if (contentType.includes('application/json')) {
        body = await resp.json().catch(() => null);
      } else {
        body = await resp.text().catch(() => '');
      }

      return { ok: resp.ok, status: resp.status, statusText: resp.statusText, data: body };
    }, {
      method,
      requestPath: normalizeApiPath(requestPath),
      data,
      options,
      csrf: csrfToken,
    });

    const responseText = typeof response.data === 'string' ? response.data : '';
    const isHtmlResponse = /<html|<!doctype html/i.test(responseText);
    const isRetryableServerError = responseText
      && (
        response.status >= 500
        && /Server Error|OperationalError|Can't connect to MySQL server|Name or service not known|Bad Gateway|Service(?: Temporarily)? Unavailable|Gateway Timeout|503|系统出现异常|努力恢复中|请稍后再试/i.test(responseText)
        || response.status === 404
        && isHtmlResponse
        && /页面找不到|404页|404 page|page not found/i.test(responseText)
      );
    if (!isRetryableServerError || attempt === maxAttempts) {
      const isUnauthenticated = response.status === 401
        && JSON.stringify(response.data || '').includes('UNAUTHENTICATED');
      if (isUnauthenticated && options.retryAuth !== false && attempt === 1) {
        await reAuth(page);
        continue;
      }
      break;
    }
    await page.waitForTimeout(Math.min(15000, 3000 * attempt));
  }

  if (!response.ok && !options.allowFailure) {
    throw new Error(`${method} ${normalizeApiPath(requestPath)} failed: ${response.status} ${response.statusText} ${JSON.stringify(response.data)}`);
  }

  return response;
}

const pageApiGet = (page, requestPath, query, options) => apiRequest(page, 'GET', requestPath, query, options);
const pageApiPost = (page, requestPath, data, options) => apiRequest(page, 'POST', requestPath, data, options);
const pageApiPut = (page, requestPath, data, options) => apiRequest(page, 'PUT', requestPath, data, options);
const pageApiPatch = (page, requestPath, data, options) => apiRequest(page, 'PATCH', requestPath, data, options);
const pageApiDelete = (page, requestPath, data, options) => apiRequest(page, 'DELETE', requestPath, data, options);

function unwrapApiData(response) {
  const body = response && response.data;
  if (body && Object.prototype.hasOwnProperty.call(body, 'data')) {
    return body.data;
  }
  return body;
}

function unwrapApiResults(response) {
  const data = unwrapApiData(response);
  if (Array.isArray(data)) return data;
  if (Array.isArray(data && data.results)) return data.results;
  return [];
}

function defaultBackendConfig(host = 'httpbin.org') {
  return {
    type: 'node',
    timeout: 30,
    loadbalance: 'roundrobin',
    hosts: [{ scheme: 'http', host, weight: 100 }],
  };
}

async function listStages(page, gatewayId) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/stages/`));
}

async function listBackends(page, gatewayId) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/backends/`));
}

async function listResources(page, gatewayId) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resources/`));
}

async function getDefaultBackend(page, gatewayId) {
  const backends = await listBackends(page, gatewayId);
  const backend = backends.find(item => item.is_default) || backends[0];
  if (!backend) {
    throw new Error(`No backend service found for gateway ${gatewayId}`);
  }
  return backend;
}

async function getDefaultStage(page, gatewayId) {
  const stages = await listStages(page, gatewayId);
  const stage = stages.find(item => item.name === 'prod')
    || stages.find(item => item.resource_version && item.resource_version.id)
    || stages[0];
  if (!stage) {
    throw new Error(`No stage found for gateway ${gatewayId}`);
  }
  return stage;
}

async function createTestStage(page, gatewayId, options = {}) {
  const name = options.name || createTestIdentifier('bdd_stage', { maxLength: 20 });
  const backends = await listBackends(page, gatewayId);
  if (backends.length === 0) {
    throw new Error(`No backend service found for creating stage ${name}`);
  }

  const host = options.host || 'httpbin.org';
  const payload = {
    name,
    description: options.description || `BDD stage ${name}`,
    backends: backends.map(backend => ({
      id: backend.id,
      config: defaultBackendConfig(host),
    })),
  };

  await pageApiPost(page, `/gateways/${gatewayId}/stages/`, payload);
  const created = (await listStages(page, gatewayId)).find(item => item.name === name);
  if (!created) {
    throw new Error(`Stage ${name} was created but not found in stage list`);
  }
  return created;
}

async function updateTestStage(page, gatewayId, stageId, updates = {}) {
  const stages = await listStages(page, gatewayId);
  const current = stages.find(item => item.id === stageId);
  if (!current) {
    throw new Error(`Stage ${stageId} not found`);
  }

  const backends = await listBackends(page, gatewayId);
  const host = updates.host || 'httpbin.org';
  const payload = {
    name: updates.name || current.name,
    description: updates.description !== undefined ? updates.description : current.description,
    backends: backends.map(backend => ({
      id: backend.id,
      config: defaultBackendConfig(host),
    })),
  };

  return unwrapApiData(await pageApiPut(page, `/gateways/${gatewayId}/stages/${stageId}/`, payload));
}

async function cleanupStagesByName(page, gatewayId, names) {
  const nameSet = new Set([].concat(names || []).filter(Boolean));
  if (nameSet.size === 0) return;

  const stages = await listStages(page, gatewayId);
  for (const stage of stages.filter(item => nameSet.has(item.name))) {
    await pageApiDelete(page, `/gateways/${gatewayId}/stages/${stage.id}/`, null, { allowFailure: true });
  }
}

async function createTestResource(page, gatewayId, options = {}) {
  const name = options.name || createTestIdentifier('bdd_resource');
  const backend = options.backend || await getDefaultBackend(page, gatewayId);
  const method = options.method || 'GET';
  const pathValue = options.path || `/${name}`;
  const payload = {
    name,
    description: options.description || `BDD resource ${name}`,
    method,
    path: pathValue,
    match_subpath: false,
    is_public: true,
    allow_apply_permission: true,
    backend: {
      id: backend.id,
      config: {
        method,
        path: options.backendPath || '/get',
        timeout: 30,
      },
    },
    auth_config: {
      app_verified_required: true,
      auth_verified_required: true,
      resource_perm_required: false,
    },
    label_ids: options.label_ids || [],
  };

  await pageApiPost(page, `/gateways/${gatewayId}/resources/`, payload);
  const created = (await listResources(page, gatewayId)).find(item => item.name === name);
  if (!created) {
    throw new Error(`Resource ${name} was created but not found in resource list`);
  }
  return created;
}

async function cleanupResourcesByName(page, gatewayId, names) {
  const nameSet = new Set([].concat(names || []).filter(Boolean));
  if (nameSet.size === 0) return;

  const resources = await listResources(page, gatewayId);
  for (const resource of resources.filter(item => nameSet.has(item.name))) {
    await pageApiDelete(page, `/gateways/${gatewayId}/resources/${resource.id}/`, null, { allowFailure: true });
  }
}

async function createTestVersion(page, gatewayId, options = {}) {
  if (options.createResource !== false) {
    await createTestResource(page, gatewayId, { name: options.resourceName });
  }

  const nextVersion = unwrapApiData(await pageApiGet(page, `/gateways/${gatewayId}/resource-versions/next-version/`));
  const payload = {
    version: options.version || nextVersion.version,
    comment: options.comment || 'BDD generated resource version',
  };
  await pageApiPost(page, `/gateways/${gatewayId}/resource-versions/`, payload);
  const created = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resource-versions/`))
    .find(item => item.version === payload.version);
  if (!created) {
    throw new Error(`Resource version ${payload.version} was created but not found in version list`);
  }
  return created;
}

async function cleanupVersionsByVersion(page, gatewayId, versions) {
  const versionSet = new Set([].concat(versions || []).filter(Boolean));
  if (versionSet.size === 0) return;

  const existing = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resource-versions/`));
  for (const version of existing.filter(item => versionSet.has(item.version))) {
    await pageApiDelete(page, `/gateways/${gatewayId}/resource-versions/${version.id}/`, null, { allowFailure: true });
  }
}

async function createResourceDoc(page, gatewayId, resourceId, options = {}) {
  const payload = {
    language: options.language || 'zh',
    content: options.content || '# BDD resource doc\n\nThis document is generated by test-bdd.',
  };
  return unwrapApiData(await pageApiPost(page, `/gateways/${gatewayId}/resources/${resourceId}/docs/`, payload));
}

async function cleanupResourceDocs(page, gatewayId, resourceId) {
  const docs = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/resources/${resourceId}/docs/`, null, { allowFailure: true }));
  for (const doc of docs.filter(item => item.id)) {
    await pageApiDelete(page, `/gateways/${gatewayId}/resources/${resourceId}/docs/${doc.id}/`, null, { allowFailure: true });
  }
}

async function listGatewayPermissions(page, gatewayId, bkAppCode) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/permissions/app-permissions/`, { bk_app_code: bkAppCode }));
}

async function createGatewayPermission(page, gatewayId, options = {}) {
  const resource = options.resource || await createTestResource(page, gatewayId, { name: options.resourceName });
  const bkAppCode = options.bkAppCode || `bddapp${Date.now().toString(36).slice(-8)}`;
  const expireDays = options.expireDays || 180;

  await pageApiPost(page, `/gateways/${gatewayId}/permissions/app-gateway-permissions/`, {
    bk_app_code: bkAppCode,
    expire_days: expireDays,
    resource_ids: [resource.id],
  });
  await pageApiPost(page, `/gateways/${gatewayId}/permissions/app-resource-permissions/`, {
    bk_app_code: bkAppCode,
    expire_days: expireDays,
    resource_ids: [resource.id],
  });

  return { bkAppCode, resource };
}

async function cleanupPermissionsByAppCode(page, gatewayId, bkAppCode) {
  const permissions = await listGatewayPermissions(page, gatewayId, bkAppCode);
  const gatewayIds = permissions
    .filter(item => item.grant_dimension === 'api')
    .map(item => item.id);
  const resourceIds = permissions
    .filter(item => item.grant_dimension === 'resource')
    .map(item => item.id);

  if (gatewayIds.length > 0) {
    await pageApiDelete(page, `/gateways/${gatewayId}/permissions/app-gateway-permissions/delete/`, { ids: gatewayIds }, { allowFailure: true, query: true });
  }
  if (resourceIds.length > 0) {
    await pageApiDelete(page, `/gateways/${gatewayId}/permissions/app-resource-permissions/delete/`, { ids: resourceIds }, { allowFailure: true, query: true });
  }
}

async function createAlarmStrategy(page, gatewayId, options = {}) {
  const name = options.name || createTestName('bdd-alarm');
  const payload = {
    name,
    alarm_type: 'resource_backend',
    alarm_subtype: options.alarm_subtype || 'status_code_5xx',
    gateway_label_ids: [],
    effective_stages: options.effective_stages || [],
    config: {
      detect_config: {
        duration: 1,
        method: 'gte',
        count: 1,
      },
      converge_config: {
        duration: 0,
      },
      notice_config: {
        notice_way: ['wechat'],
        notice_role: ['maintainer'],
        notice_extra_receiver: [],
      },
    },
  };

  await pageApiPost(page, `/gateways/${gatewayId}/monitors/alarm/strategies/`, payload);
  const created = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/monitors/alarm/strategies/`))
    .find(item => item.name === name);
  if (!created) {
    throw new Error(`Alarm strategy ${name} was created but not found in strategy list`);
  }
  return created;
}

async function cleanupAlarmStrategiesByName(page, gatewayId, names) {
  const nameSet = new Set([].concat(names || []).filter(Boolean));
  if (nameSet.size === 0) return;

  const strategies = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/monitors/alarm/strategies/`));
  for (const strategy of strategies.filter(item => nameSet.has(item.name))) {
    await pageApiDelete(page, `/gateways/${gatewayId}/monitors/alarm/strategies/${strategy.id}/`, null, { allowFailure: true });
  }
}

async function createTestMcpServer(page, gatewayId, options = {}) {
  const name = options.name || createTestName('bdd-mcp');
  const stage = options.stage || await getDefaultStage(page, gatewayId);
  if (options.ensurePublished !== false) {
    const version = await createTestVersion(page, gatewayId, {
      createResource: false,
      comment: `BDD MCP publish ${name}`,
    });
    await pageApiPost(page, `/gateways/${gatewayId}/releases/`, {
      stage_id: stage.id,
      resource_version_id: version.id,
      comment: `BDD MCP publish ${name}`,
    });
  }

  const resources = await listResources(page, gatewayId);
  const resource = options.resource
    || resources.find(item => item.name === options.resourceName)
    || resources.find(item => /^test_resource_/.test(item.name))
    || resources[0];
  if (!resource) {
    throw new Error('No resource found for creating MCP Server');
  }

  const payload = {
    name,
    title: options.title || `BDD MCP ${name}`,
    description: options.description || `BDD MCP Server ${name}`,
    stage_id: stage.id,
    is_public: true,
    labels: [],
    resource_names: [resource.name],
    tool_names: [resource.name],
    prompts: [],
    protocol_type: options.protocol_type || 'sse',
    category_ids: [],
    oauth2_public_client_enabled: false,
    raw_response_enabled: false,
  };

  return unwrapApiData(await pageApiPost(page, `/gateways/${gatewayId}/mcp-servers/`, payload));
}

async function cleanupMcpServersByName(page, gatewayId, names) {
  const nameSet = new Set([].concat(names || []).filter(Boolean));
  if (nameSet.size === 0) return;

  const servers = unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/mcp-servers/`));
  for (const server of servers.filter(item => nameSet.has(item.name))) {
    await pageApiDelete(page, `/gateways/${gatewayId}/mcp-servers/${server.id}/`, null, { allowFailure: true });
  }
}

const cleanupByName = {
  stages: cleanupStagesByName,
  resources: cleanupResourcesByName,
  versions: cleanupVersionsByVersion,
  alarmStrategies: cleanupAlarmStrategiesByName,
  mcpServers: cleanupMcpServersByName,
};

module.exports = {
  RUNTIME_ENV_FILE,
  STORAGE_STATE_FILE,
  TABLE_ROW_SELECTOR,
  GATEWAY_LIST_SELECTOR,
  PLUGIN_BINDING_SELECTOR,
  PLUGIN_SELECTION_SELECTOR,
  login,
  reAuth,
  waitForPageReady,
  waitForGatewayHomeReady,
  navigateToGatewayPage,
  openStageOverviewTab,
  navigateToStageOverviewTab,
  fillForm,
  selectDropdown,
  selectDropdownOption,
  dismissFloatingLayers,
  closeSlider,
  getToastMessage,
  getVisibleTableRows,
  getGatewayListItems,
  getGatewayListItemByText,
  getFirstVisibleTableRow,
  getTableRowByText,
  getTableRowActionButton,
  selectVisibleTableRowCheckboxes,
  getFirstResourcePluginCountLink,
  openFirstResourcePluginPanel,
  getActiveOverlay,
  getActiveSideslider,
  getActiveDialog,
  getActionButton,
  getPluginBindingItems,
  getPluginBindingItemByText,
  getPluginSelectionOptions,
  getPluginSelectionOptionByText,
  getAvailablePluginSelectionOption,
  clickConfirm,
  getTableRowCount,
  isSessionExpired,
  getGatewayId,
  apiRequest,
  pageApiGet,
  pageApiPost,
  pageApiPut,
  pageApiPatch,
  pageApiDelete,
  unwrapApiData,
  unwrapApiResults,
  listStages,
  listBackends,
  listResources,
  getDefaultStage,
  getDefaultBackend,
  createTestStage,
  updateTestStage,
  createTestResource,
  createTestVersion,
  createResourceDoc,
  createGatewayPermission,
  createAlarmStrategy,
  createTestMcpServer,
  listGatewayPermissions,
  cleanupStagesByName,
  cleanupResourcesByName,
  cleanupVersionsByVersion,
  cleanupResourceDocs,
  cleanupPermissionsByAppCode,
  cleanupAlarmStrategiesByName,
  cleanupMcpServersByName,
  cleanupByName,
  extractCsrfTokenFromCookieString,
  getCsrfToken,
  hasAuthenticatedSession,
  waitForAuthenticatedSession,
  readRuntimeState,
  writeRuntimeState,
  cleanupRuntimeArtifacts,
  sanitizeTestName,
  createTestName,
  createTestIdentifier,
  attachHardFailureGuard,
  clearHardFailureGuard,
  assertNoHardFailure,
  waitForPageReadyAndAssert,
  BASE_URL,
};
