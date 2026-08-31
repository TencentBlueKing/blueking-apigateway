const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const ENV_JSON = path.join(__dirname, '.test-env.json');
const config = JSON.parse(fs.readFileSync(ENV_JSON, 'utf-8'));
const BASE_URL = config.url;

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Login
  await page.goto(BASE_URL);
  await page.waitForTimeout(3000);
  if (page.url().includes('/login/')) {
    await page.locator('input[placeholder="请输入用户名"]').fill(config.user);
    await page.locator('input[placeholder="请输入密码"]').fill(config.password);
    await page.locator('button').filter({ hasText: '立即登录' }).click();
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);
      if (!page.url().includes('/login/')) break;
    }
  }
  await page.goto(BASE_URL);
  await page.waitForTimeout(2000);

  const csrf = await page.evaluate(() => {
    const m = document.cookie.match(/(?:bkapigw_csrftoken[^=]*|bk_csrftoken|csrftoken)=([^;]+)/);
    return m ? m[1] : '';
  });

  // List gateways, find orphaned aigw-* and testagent-* ones
  const result = await page.evaluate(async (csrf) => {
    const resp = await fetch('/backend/gateways/?limit=10000', { credentials: 'include', headers: { 'X-CSRFToken': csrf } });
    const data = await resp.json();
    return data;
  }, csrf);

  const gateways = result.data?.results || result.data || [];
  const orphans = gateways.filter(g => /^aigw-/.test(g.name));
  console.log('Found orphaned AI gateways:', orphans.map(g => `${g.name}(id=${g.id})`).join(', '));

  for (const gw of orphans) {
    // Deactivate
    await page.evaluate(async ({ id, csrf }) => {
      await fetch(`/backend/gateways/${id}/status/`, {
        method: 'PUT', credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ status: 0 }),
      });
    }, { id: gw.id, csrf });
    await page.waitForTimeout(2000);
    // Delete
    const delResp = await page.evaluate(async ({ id, csrf }) => {
      const resp = await fetch(`/backend/gateways/${id}/`, {
        method: 'DELETE', credentials: 'include',
        headers: { 'X-CSRFToken': csrf },
      });
      return { ok: resp.ok, status: resp.status };
    }, { id: gw.id, csrf });
    console.log(`  Deleted ${gw.name}(id=${gw.id}): ${delResp.status}`);
  }

  await browser.close();
  console.log('Cleanup done');
})();
