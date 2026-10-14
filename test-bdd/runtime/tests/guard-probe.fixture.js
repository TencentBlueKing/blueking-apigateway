// Deliberately failing probes. Run only with guard-integration.config.js.
const { test } = require('../bdd-test');

test('guard detects an exception after an otherwise successful test', async ({ page }) => {
  await page.goto('data:text/html,<main>Loaded</main>');
  await page.evaluate(() => { setTimeout(() => { throw new Error('BDD_PROBE_UNCAUGHT'); }, 0); });
  await page.waitForTimeout(100);
});

test('guard detects failed API behind a visible table', async ({ page }) => {
  await page.route('https://bdd-probe.test/**', route => route.fulfill({
    status: route.request().url().endsWith('/backend/data/') ? 500 : 200,
    contentType: 'text/html',
    body: '<table><tr><td>Empty</td></tr></table>',
  }));
  await page.goto('https://bdd-probe.test/');
  await page.evaluate(() => fetch('/backend/data/'));
});

test('guard detects an API failure arriving after the UI is visible', async ({ page }) => {
  await page.route('https://bdd-probe.test/**', async route => {
    const delayed = route.request().url().endsWith('/backend/delayed/');
    if (delayed) await new Promise(resolve => setTimeout(resolve, 800));
    await route.fulfill({ status: delayed ? 500 : 200, contentType: 'text/html', body: '<main>Loaded</main>' });
  });
  await page.goto('https://bdd-probe.test/');
  await page.evaluate(() => { void fetch('/backend/delayed/'); });
});
