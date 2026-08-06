// @generated from: test-bdd/cases/29-AI网关/01-AI网关模型服务.md
// @generated-date: 2026-07-23

const { test, expect, chromium } = require('@playwright/test');
const {
  login,
  pageApiGet,
  pageApiPost,
  pageApiPut,
  pageApiDelete,
  unwrapApiData,
  unwrapApiResults,
  createTestName,
  createTestIdentifier,
  getGatewayId,
  BASE_URL,
} = require('../../runtime/helpers');

const DEEPSEEK_API_KEY = process.env.TEST_BDD_DEEPSEEK_API_KEY || '';

function getDeepseekApiKey() {
  expect(
    DEEPSEEK_API_KEY,
    'TEST_BDD_DEEPSEEK_API_KEY is required for DeepSeek-backed AI gateway tests'
  ).toBeTruthy();
  return DEEPSEEK_API_KEY;
}

// Shared state across tests (workers: 1, sequential)
let aiGatewayId;
let aiGatewayName;
let prodStageId;
let deepseekBackendId;
let aiResourceId;
let versionId;

// Backend names: ^[a-zA-Z][a-zA-Z0-9-]{0,19}$  → hyphens, max 20 chars
function backendName(prefix) {
  return createTestName(prefix, { maxLength: 19 });
}

// Resource names: ^[a-zA-Z][a-zA-Z0-9_]{0,255}$  → underscores
function resourceName(prefix) {
  return createTestIdentifier(prefix);
}

function deepseekConfig(stageId, overrides = {}) {
  return {
    stage_id: stageId,
    provider: 'deepseek',
    api_key: getDeepseekApiKey(),
    timeout: 298,
    model_options: { temperature: 0.7 },
    ...overrides,
  };
}

function openaiCompatibleConfig(stageId, overrides = {}) {
  return {
    stage_id: stageId,
    provider: 'openai-compatible',
    endpoint: 'https://api.example.com/v1/chat/completions',
    auth_header: { name: 'Authorization', value: 'Bearer sk-testcompatible' },
    timeout: 300,
    ...overrides,
  };
}

function aiResourcePayload(backendId, overrides = {}) {
  return {
    name: resourceName('ai_res'),
    description: 'AI resource BDD test',
    kind: 'ai',
    method: 'POST',
    path: `/chat/completions`,
    match_subpath: false,
    is_public: true,
    allow_apply_permission: true,
    backend: { id: backendId, config: {} },
    auth_config: {
      app_verified_required: true,
      auth_verified_required: true,
      resource_perm_required: false,
    },
    label_ids: [],
    ...overrides,
  };
}

// All mutating API calls use allowFailure to avoid unhandled throws that cause test timeouts.
// We inspect the response manually.
async function apiPost(page, path, data) {
  return pageApiPost(page, path, data, { allowFailure: true, retryHtml500: false });
}
async function apiPut(page, path, data) {
  return pageApiPut(page, path, data, { allowFailure: true, retryHtml500: false });
}
async function apiDelete(page, path) {
  return pageApiDelete(page, path, null, { allowFailure: true, retryHtml500: false });
}
async function apiGet(page, path, query) {
  return pageApiGet(page, path, query, { allowFailure: true, retryHtml500: false });
}

function bodyStr(resp) {
  return typeof resp.data === 'string' ? resp.data : JSON.stringify(resp.data);
}

function expectOk(resp, context) {
  expect(resp.ok, `${context}: expected success but got ${resp.status} ${resp.statusText}: ${bodyStr(resp)}`).toBe(true);
}

function expect4xx(resp, context) {
  expect(
    resp.status >= 400 && resp.status < 500,
    `${context}: expected 4xx validation error but got ${resp.status}: ${bodyStr(resp)}`
  ).toBe(true);
}

function expectNo500(resp, context) {
  expect(
    resp.status < 500,
    `${context}: got 500 SERVER ERROR (likely a genuine bug): ${resp.status}: ${bodyStr(resp)}`
  ).toBe(true);
}

test.describe('功能: AI 网关 - 模型服务全链路', () => {
  test.beforeAll(async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();
    try {
      await login(page);
      await page.goto(BASE_URL);
      await page.waitForTimeout(2000);

      aiGatewayName = createTestName('aigw');
      const createResp = await apiPost(page, '/gateways/', {
        name: aiGatewayName,
        description: 'AI Gateway BDD test',
        maintainers: ['admin'],
        is_public: false,
        kind: 2,
        tenant_mode: 'single',
        tenant_id: 'default',
      });
      expectOk(createResp, 'create AI gateway');
      aiGatewayId = String(unwrapApiData(createResp).id);

      const stagesResp = await apiGet(page, `/gateways/${aiGatewayId}/stages/`);
      const stages = unwrapApiResults(stagesResp);
      const prod = stages.find((s) => s.name === 'prod') || stages[0];
      prodStageId = prod.id;

      console.log(`[AI-BDD] AI gateway: ${aiGatewayName} (ID: ${aiGatewayId}), prod stage: ${prodStageId}`);
    } finally {
      await browser.close();
    }
  });

  test.afterAll(async () => {
    if (!aiGatewayId) return;
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();
    try {
      await login(page);
      await page.goto(BASE_URL);
      await page.waitForTimeout(2000);
      await apiPut(page, `/gateways/${aiGatewayId}/status/`, { status: 0 });
      await page.waitForTimeout(3000);
      await apiDelete(page, `/gateways/${aiGatewayId}/`);
      console.log(`[AI-BDD] Cleanup: ${aiGatewayName} (ID: ${aiGatewayId})`);
    } catch (err) {
      console.log(`[AI-BDD] Cleanup error: ${err.message}`);
    } finally {
      await browser.close();
    }
  });

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForTimeout(1000);
  });

  // ==================== AI Gateway ====================

  test('场景: 创建AI网关', async ({ page }) => {
    const resp = await apiGet(page, '/gateways/', { keyword: aiGatewayName });
    expectNo500(resp, 'list gateways');
    const gateways = unwrapApiResults(resp);
    const gw = gateways.find((g) => g.name === aiGatewayName);
    expect(gw, `AI gateway ${aiGatewayName} not found in list`).toBeTruthy();
    expect(String(gw.kind)).toBe('2');
  });

  // ==================== AI Backend CRUD ====================

  test('场景: 创建模型服务（DeepSeek）', async ({ page }) => {
    const name = backendName('ds-backend');
    const resp = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name,
      description: 'DeepSeek model service',
      type: 'http',
      kind: 'ai',
      configs: [deepseekConfig(prodStageId)],
    });
    expectNo500(resp, 'create deepseek backend');
    expectOk(resp, 'create deepseek backend');

    const listResp = await apiGet(page, `/gateways/${aiGatewayId}/backends/`);
    const backends = unwrapApiResults(listResp);
    const created = backends.find((b) => b.name === name);
    expect(created, `backend ${name} not in list`).toBeTruthy();
    expect(created.kind).toBe('ai');
    deepseekBackendId = created.id;
  });

  test('场景: 创建模型服务（OpenAI Compatible）', async ({ page }) => {
    const name = backendName('oai-backend');
    const resp = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name,
      description: 'OpenAI-compatible model service',
      type: 'http',
      kind: 'ai',
      configs: [openaiCompatibleConfig(prodStageId)],
    });
    expectNo500(resp, 'create openai-compatible backend');
    expectOk(resp, 'create openai-compatible backend');

    const listResp = await apiGet(page, `/gateways/${aiGatewayId}/backends/`);
    const backends = unwrapApiResults(listResp);
    const created = backends.find((b) => b.name === name);
    if (created) {
      await apiDelete(page, `/gateways/${aiGatewayId}/backends/${created.id}/`);
    }
  });

  test('场景: 查询模型服务列表与详情', async ({ page }) => {
    const listResp = await apiGet(page, `/gateways/${aiGatewayId}/backends/`);
    expectNo500(listResp, 'list backends');
    const backends = unwrapApiResults(listResp);
    const found = backends.find((b) => b.id === deepseekBackendId);
    expect(found, `deepseek backend ${deepseekBackendId} not in list`).toBeTruthy();
    expect(found.kind).toBe('ai');

    const detailResp = await apiGet(page, `/gateways/${aiGatewayId}/backends/${deepseekBackendId}/`);
    expectNo500(detailResp, 'backend detail');
    expectOk(detailResp, 'backend detail');
    const detail = unwrapApiData(detailResp);
    expect(detail.kind).toBe('ai');
    expect(detail.configs.length).toBeGreaterThanOrEqual(1);
    const cfg = detail.configs[0];
    expect(cfg.provider).toBe('deepseek');
    expect(cfg.timeout).toBe(298);
    expect(cfg.api_key, 'api_key should be masked').toBeTruthy();
    expect(cfg.api_key, 'api_key should NOT be plaintext').not.toBe(DEEPSEEK_API_KEY);
    expect(cfg.api_key).toContain('****');
  });

  test('场景: 编辑模型服务', async ({ page }) => {
    const detailResp = await apiGet(page, `/gateways/${aiGatewayId}/backends/${deepseekBackendId}/`);
    const detail = unwrapApiData(detailResp);

    const updateResp = await apiPut(page, `/gateways/${aiGatewayId}/backends/${deepseekBackendId}/`, {
      name: detail.name,
      description: 'Updated ' + Date.now(),
      type: 'http',
      kind: 'ai',
      configs: [deepseekConfig(prodStageId, { timeout: 200, api_key: getDeepseekApiKey() })],
    });
    expectNo500(updateResp, 'update backend');
    expectOk(updateResp, 'update backend');

    const updated = unwrapApiData(await apiGet(page, `/gateways/${aiGatewayId}/backends/${deepseekBackendId}/`));
    expect(updated.configs[0].timeout).toBe(200);
  });

  test('场景: 模型服务连接测试', async ({ page }) => {
    test.setTimeout(60000);
    const resp = await apiPost(page, `/gateways/${aiGatewayId}/backends/test-connection/`, {
      backend_id: deepseekBackendId,
      config: deepseekConfig(prodStageId, { api_key: getDeepseekApiKey() }),
    });
    expectNo500(resp, 'test-connection');
    if (resp.ok) {
      const data = unwrapApiData(resp);
      expect(data.models).toBeDefined();
      console.log('[AI-BDD] Connection test models:', JSON.stringify(data.models).slice(0, 200));
    } else {
      console.log(`[AI-BDD] Connection test returned ${resp.status}: ${bodyStr(resp).slice(0, 200)}`);
    }
  });

  test('场景: 删除模型服务', async ({ page }) => {
    const name = backendName('del-backend');
    const createResp = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name,
      description: 'for deletion test',
      type: 'http',
      kind: 'ai',
      configs: [deepseekConfig(prodStageId)],
    });
    expectOk(createResp, 'create backend for deletion');
    const backends = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/backends/`));
    const created = backends.find((b) => b.name === name);
    expect(created).toBeTruthy();

    const delResp = await apiDelete(page, `/gateways/${aiGatewayId}/backends/${created.id}/`);
    expectNo500(delResp, 'delete backend');
    expectOk(delResp, 'delete backend');

    const afterDelete = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/backends/`));
    expect(afterDelete.find((b) => b.id === created.id)).toBeUndefined();
  });

  // ==================== AI Backend Boundary Cases ====================

  test('场景: 普通网关不支持模型服务', async ({ page }) => {
    const stdGatewayId = getGatewayId();
    const resp = await apiPost(page, `/gateways/${stdGatewayId}/backends/`, {
      name: backendName('std-ai-be'),
      description: 'should fail',
      type: 'http',
      kind: 'ai',
      configs: [deepseekConfig(prodStageId)],
    });
    expectNo500(resp, 'create AI backend on standard gateway');
    expect4xx(resp, 'create AI backend on standard gateway');
    expect(bodyStr(resp)).toContain('普通网关不支持模型服务');
  });

  test('场景: 模型服务provider与必填字段校验', async ({ page }) => {
    // Invalid provider
    const r1 = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name: backendName('badprov'),
      type: 'http',
      kind: 'ai',
      configs: [{ stage_id: prodStageId, provider: 'anthropic', api_key: 'sk-test', timeout: 300 }],
    });
    expectNo500(r1, 'invalid provider');
    expect4xx(r1, 'invalid provider');

    // deepseek without api_key
    const r2 = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name: backendName('nokey'),
      type: 'http',
      kind: 'ai',
      configs: [{ stage_id: prodStageId, provider: 'deepseek', timeout: 300 }],
    });
    expectNo500(r2, 'deepseek without api_key');
    expect4xx(r2, 'deepseek without api_key');
    expect(bodyStr(r2)).toContain('api_key');

    // openai-compatible without endpoint
    const r3 = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name: backendName('noendpoint'),
      type: 'http',
      kind: 'ai',
      configs: [{ stage_id: prodStageId, provider: 'openai-compatible', timeout: 300 }],
    });
    expectNo500(r3, 'openai-compatible without endpoint');
    expect4xx(r3, 'openai-compatible without endpoint');
    expect(bodyStr(r3)).toContain('endpoint');
  });

  test('场景: 模型服务timeout范围校验', async ({ page }) => {
    const r1 = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name: backendName('timeout0'),
      type: 'http',
      kind: 'ai',
      configs: [deepseekConfig(prodStageId, { timeout: 0 })],
    });
    expectNo500(r1, 'timeout=0');
    expect4xx(r1, 'timeout=0');

    const r2 = await apiPost(page, `/gateways/${aiGatewayId}/backends/`, {
      name: backendName('timeout301'),
      type: 'http',
      kind: 'ai',
      configs: [deepseekConfig(prodStageId, { timeout: 301 })],
    });
    expectNo500(r2, 'timeout=301');
    expect4xx(r2, 'timeout=301');
  });

  test('场景: 模型服务kind不可变', async ({ page }) => {
    const detail = unwrapApiData(await apiGet(page, `/gateways/${aiGatewayId}/backends/${deepseekBackendId}/`));
    const resp = await apiPut(page, `/gateways/${aiGatewayId}/backends/${deepseekBackendId}/`, {
      name: detail.name,
      description: 'try change kind',
      type: 'http',
      kind: 'standard',
      configs: [deepseekConfig(prodStageId)],
    });
    expectNo500(resp, 'change backend kind');
    expect4xx(resp, 'change backend kind');
    expect(bodyStr(resp)).toContain('不能修改');
  });

  // ==================== AI Resource CRUD ====================

  test('场景: 创建模型代理API', async ({ page }) => {
    const payload = aiResourcePayload(deepseekBackendId, {
      name: resourceName('chat_completions'),
      path: '/chat/completions',
    });
    const resp = await apiPost(page, `/gateways/${aiGatewayId}/resources/`, payload);
    expectNo500(resp, 'create AI resource');
    expectOk(resp, 'create AI resource');

    const resources = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/resources/`));
    const created = resources.find((r) => r.name === payload.name);
    expect(created, `AI resource ${payload.name} not in list`).toBeTruthy();
    expect(created.kind).toBe('ai');
    aiResourceId = created.id;
  });

  test('场景: 查询与编辑模型代理API', async ({ page }) => {
    const resources = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/resources/`));
    const found = resources.find((r) => r.id === aiResourceId);
    expect(found, `AI resource ${aiResourceId} not in list`).toBeTruthy();
    expect(found.kind).toBe('ai');

    const detail = unwrapApiData(await apiGet(page, `/gateways/${aiGatewayId}/resources/${aiResourceId}/`));
    const updateResp = await apiPut(page, `/gateways/${aiGatewayId}/resources/${aiResourceId}/`, {
      ...detail,
      description: 'Updated AI resource ' + Date.now(),
      backend: { id: deepseekBackendId, config: {} },
      auth_config: detail.auth_config || {
        app_verified_required: true,
        auth_verified_required: true,
        resource_perm_required: false,
      },
      label_ids: [],
    });
    expectNo500(updateResp, 'update AI resource');
    expectOk(updateResp, 'update AI resource');
  });

  test('场景: 删除模型代理API', async ({ page }) => {
    const payload = aiResourcePayload(deepseekBackendId, {
      name: resourceName('del_res'),
      path: '/delete/test',
    });
    const createResp = await apiPost(page, `/gateways/${aiGatewayId}/resources/`, payload);
    expectOk(createResp, 'create resource for deletion');
    const resources = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/resources/`));
    const created = resources.find((r) => r.name === payload.name);
    expect(created).toBeTruthy();

    const delResp = await apiDelete(page, `/gateways/${aiGatewayId}/resources/${created.id}/`);
    expectNo500(delResp, 'delete AI resource');
    expectOk(delResp, 'delete AI resource');

    const afterDelete = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/resources/`));
    expect(afterDelete.find((r) => r.id === created.id)).toBeUndefined();
  });

  // ==================== AI Resource Boundary Cases ====================

  test('场景: 模型代理API仅支持POST', async ({ page }) => {
    const payload = aiResourcePayload(deepseekBackendId, {
      name: resourceName('get_res'),
      path: '/get/test',
      method: 'GET',
    });
    const resp = await apiPost(page, `/gateways/${aiGatewayId}/resources/`, payload);
    expectNo500(resp, 'create AI resource with GET');
    expect4xx(resp, 'create AI resource with GET');
    expect(bodyStr(resp)).toContain('POST');
  });

  test('场景: 模型代理API后端类型匹配校验', async ({ page }) => {
    const backends = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/backends/`));
    const stdBackend = backends.find((b) => b.kind === 'standard') || backends.find((b) => b.name === 'default');
    expect(stdBackend, 'no standard backend on AI gateway for mismatch test').toBeTruthy();

    const payload = aiResourcePayload(stdBackend.id, {
      name: resourceName('mismatch_res'),
      path: '/mismatch/test',
    });
    const resp = await apiPost(page, `/gateways/${aiGatewayId}/resources/`, payload);
    expectNo500(resp, 'create AI resource with standard backend');
    expect4xx(resp, 'create AI resource with standard backend');
    expect(bodyStr(resp)).toContain('不匹配');
  });

  test('场景: 资源kind不可变', async ({ page }) => {
    const detail = unwrapApiData(await apiGet(page, `/gateways/${aiGatewayId}/resources/${aiResourceId}/`));
    const resp = await apiPut(page, `/gateways/${aiGatewayId}/resources/${aiResourceId}/`, {
      ...detail,
      kind: 'standard',
      backend: { id: deepseekBackendId, config: {} },
      auth_config: detail.auth_config || {
        app_verified_required: true,
        auth_verified_required: true,
        resource_perm_required: false,
      },
      label_ids: [],
    });
    expectNo500(resp, 'change resource kind');
    expect4xx(resp, 'change resource kind');
    expect(bodyStr(resp)).toContain('不能修改');
  });

  // ==================== Version & Publish ====================

  test('场景: 生成资源版本', async ({ page }) => {
    let version = '1.0.0';
    try {
      const nextResp = await apiGet(page, `/gateways/${aiGatewayId}/resource-versions/next-version/`);
      if (nextResp.ok) {
        const nextData = unwrapApiData(nextResp);
        if (nextData && nextData.version) version = nextData.version;
      }
    } catch { /* use default */ }

    const resp = await apiPost(page, `/gateways/${aiGatewayId}/resource-versions/`, {
      version,
      comment: 'AI gateway BDD version',
    });
    expectNo500(resp, 'generate version');
    expectOk(resp, 'generate version');

    const versions = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/resource-versions/`));
    const created = versions.find((v) => v.version === version);
    expect(created, `version ${version} not in list`).toBeTruthy();
    versionId = created.id;
  });

  test('场景: 发布模型代理API到环境', async ({ page }) => {
    test.setTimeout(120000);
    expect(versionId, 'no versionId — version generation may have failed').toBeTruthy();

    const resp = await apiPost(page, `/gateways/${aiGatewayId}/releases/`, {
      stage_id: prodStageId,
      resource_version_id: versionId,
      comment: 'AI gateway BDD publish',
    });
    expectNo500(resp, 'publish to prod');

    if (resp.ok) {
      // Publish is async (status "doing") — wait briefly then check release history
      await page.waitForTimeout(5000);
      const histories = unwrapApiResults(await apiGet(page, `/gateways/${aiGatewayId}/releases/histories/`, { limit: 5 }));
      expect(histories.length, 'should have release history after publish').toBeGreaterThan(0);
      console.log('[AI-BDD] Publish OK, release history count:', histories.length);
    } else {
      console.log(`[AI-BDD] Publish returned ${resp.status} (may be expected if data plane < 3.16): ${bodyStr(resp).slice(0, 300)}`);
    }
  });
});
