// @generated from: test-bdd/cases/00-路由冒烟/01-全站路由冒烟.md
// @generated-date: 2026-10-14
const { test, expect } = require('../../runtime/bdd-test');
const { BASE_URL, getGatewayId, pageApiGet, unwrapApiResults } = require('../../runtime/helpers');

// Each page is an independent result. No single failed route blocks the remainder.
const gatewayPages = [
  ['stage/overview', '环境概览', '.content-view', 'prod'],
  ['stage/release-record', '发布记录', '.content-view', '发布'],
  ['resource/setting', '资源配置', '.content-view', '新建'],
  ['resource/create', '新建资源', '.content-view', '基础信息'],
  ['resource/import', '导入资源配置', '.content-view', '校验文件'],
  ['resource/import-doc', '导入资源文档', '.content-view', '上传文件'],
  ['resource/version', '资源版本', '.content-view', '版本列表'],
  ['basic-info', '基本信息', '.content-view', 'API公钥'],
  ['members', '成员管理', '.content-view', '新增成员'],
  ['backend', '后端服务', '.content-view', 'default'],
  ['permission/apply', '权限审批', '.content-view', '批量审批'],
  ['permission/record', '审批历史', '.content-view', '审批状态'],
  ['permission/app', '应用权限', '.content-view', '主动授权'],
  ['log', '流水日志', '.content-view', '日志详情'],
  ['dashboard', '仪表盘', '.content-view', '选择时间'],
  ['report', '统计报表', '.content-view', '环境'],
  ['online-debugging', '在线调试', '.content-view', '请求'],
  ['audit', '操作记录', '.content-view', '操作'],
  ['monitor/alarm-strategy', '告警策略', '.content-view', '新建'],
  ['monitor/alarm-history', '告警记录', '.content-view', '告警'],
  ['mcp/server', 'MCP Server', '.content-view', '批量复制'],
  ['mcp/permission', 'MCP权限', '.content-view', '权限'],
  ['mcp/observability', 'MCP可观测', '.content-view', '日志详情'],
];
const globalPages = [
  ['/', '网关首页', 'body', '新建网关'],
  ['/create-gateway', '新建网关', 'body', '网关类型'],
  ['/platform-tools/toolbox', '工具箱', 'body', '工具'],
  ['/platform-tools/automated-gateway', '自动化接入网关', 'body', '自动化'],
  ['/platform-tools/bk-cli', '平台工具BK-CLI', 'body', 'CLI'],
  ['/platform-tools/programmable-gateway', '可编程网关', 'body', '可编程'],
  ['/platform-tools/micro-gateway', '蓝鲸微网关', 'body', '微网关'],
  ['/bk-cli', '独立BK-CLI', 'body', 'CLI'],
  ['/docs/api-docs/gateway', '网关API文档', 'body', '网关负责人'],
  ['/docs/api-docs/component', '组件API文档', 'body', '请输入 API 名称'],
  ['/mcp-market', 'MCP市场', 'body', '批量复制'],
  ['/personal-workbench/my-apply', '我的申请', 'body', '授权维度'],
  ['/personal-workbench/my-pending', '我的待办', 'body', '批量审批'],
  ['/personal-workbench/my-handled', '我的已办', 'body', '审批状态'],
];

async function visit(page, path, selector, text) {
  const response = await page.goto(`${BASE_URL.replace(/\/$/, '')}${path}`, { waitUntil: 'domcontentloaded' });
  expect(response.status(), `Document ${path}`).toBe(200);
  await expect.poll(() => new URL(page.url()).pathname).toBe(path);
  if (text === '请输入 API 名称') await expect(page.getByPlaceholder(text)).toBeVisible();
  else await expect(page.locator(selector)).toContainText(text, { timeout: 15000 });
  await expect(page.locator('.bk-loading-mask:visible')).toHaveCount(0, { timeout: 15000 });
}

test.describe('功能: 全站路由冒烟 - 独立深链接与内容检查', () => {
  for (const [path, title, selector, text] of gatewayPages) {
    test(`场景: 深链接 - ${title}`, async ({ page }) => {
      await visit(page, `/${getGatewayId()}/${path}`, selector, text);
    });
  }
  for (const [path, title, selector, text] of globalPages) {
    test(`场景: 深链接 - ${title}`, async ({ page }) => {
      await visit(page, path, selector, text);
    });
  }
  for (const mode of ['edit', 'clone']) {
    test(`场景: 资源动态路由 - ${mode}`, async ({ page }) => {
      await page.goto(BASE_URL);
      const resources = unwrapApiResults(await pageApiGet(page, `/gateways/${getGatewayId()}/resources/`, { limit: 100 }));
      expect(resources.length, 'Setup must supply a resource; do not silently omit dynamic routes').toBeGreaterThan(0);
      await visit(page, `/${getGatewayId()}/resource/${mode}/${resources[0].id}`, '.content-view', '基础信息');
      await expect(page.locator('input[placeholder*="字母"]').first()).not.toHaveValue('');
    });
  }
});
