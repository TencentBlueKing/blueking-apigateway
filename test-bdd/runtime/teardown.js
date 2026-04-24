// test-bdd/scripts/teardown.js
// Global teardown: delete the test gateway created during setup.
// This runs once after all tests via Playwright's globalTeardown.

const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const { BASE_URL, USERNAME, PASSWORD } = require('./test-env');
const ENV_FILE = path.join(__dirname, '.env');
const STORAGE_FILE = path.join(__dirname, 'storage-state.json');

module.exports = async () => {
  // Read gateway info from .env
  let gatewayId, gatewayName;
  try {
    const envContent = fs.readFileSync(ENV_FILE, 'utf-8');
    const idMatch = envContent.match(/TEST_GATEWAY_ID=(\d+)/);
    const nameMatch = envContent.match(/TEST_GATEWAY_NAME=(\S+)/);
    gatewayId = idMatch ? idMatch[1] : null;
    gatewayName = nameMatch ? nameMatch[1] : null;
  } catch {
    console.log('[teardown] No .env file found — skipping cleanup');
    return;
  }

  if (!gatewayId) {
    console.log('[teardown] No gateway ID found — skipping cleanup');
    return;
  }

  console.log(`[teardown] Cleaning up gateway: ${gatewayName} (ID: ${gatewayId})`);

  const browser = await chromium.launch();
  let context;

  // Reuse storage state if available
  try {
    const storageState = JSON.parse(fs.readFileSync(STORAGE_FILE, 'utf-8'));
    context = await browser.newContext({ storageState });
  } catch {
    context = await browser.newContext();
  }

  const page = await context.newPage();

  try {
    // Navigate to gateway basic info
    await page.goto(`${BASE_URL}/${gatewayId}/basic-info`);
    await page.waitForTimeout(2000);

    // Re-authenticate if needed
    if (page.url().includes('/login/')) {
      const hasChineseForm = await page.locator('input[placeholder="请输入用户名"]').isVisible().catch(() => false);
      if (hasChineseForm) {
        await page.locator('input[placeholder="请输入用户名"]').click();
        await page.locator('input[placeholder="请输入用户名"]').type(USERNAME);
        await page.locator('input[placeholder="请输入密码"]').click();
        await page.locator('input[placeholder="请输入密码"]').type(PASSWORD);
        await page.locator('button').filter({ hasText: '立即登录' }).click();
      }

      for (let i = 0; i < 30; i++) {
        await page.waitForTimeout(500);
        if (!page.url().includes('/login/')) break;
      }

      await page.goto(`${BASE_URL}/${gatewayId}/basic-info`);
      await page.waitForTimeout(2000);
    }

    // Step 1: Deactivate (停用) if the button is visible
    const deactivateBtn = page.locator('button').filter({ hasText: '停用' }).first();
    if (await deactivateBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await deactivateBtn.click({ force: true });
      await page.waitForTimeout(1000);

      // Confirm deactivation dialog
      const confirmBtn = page.locator('.bk-dialog button, .bk-infobox button').filter({ hasText: /确定|确认/ }).first();
      if (await confirmBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await confirmBtn.click({ force: true });
        await page.waitForTimeout(2000);
      }

      console.log('[teardown] Gateway deactivated');
    }

    // Step 2: Delete (删除)
    const deleteBtn = page.locator('button').filter({ hasText: /^删除$/ }).first();
    if (await deleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await deleteBtn.click({ force: true });
      await page.waitForTimeout(1000);

      // Confirm deletion — may require typing gateway name
      const nameConfirmInput = page.locator('.bk-dialog input, .bk-infobox input').first();
      if (await nameConfirmInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await nameConfirmInput.fill(gatewayName || '');
        await page.waitForTimeout(300);
      }

      const confirmDelete = page.locator('.bk-dialog button, .bk-infobox button').filter({ hasText: /确定|确认|删除/ }).first();
      if (await confirmDelete.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmDelete.click({ force: true });
        await page.waitForTimeout(3000);
      }

      console.log('[teardown] Gateway deleted');
    }

    // Step 3: Verify deletion — search home page
    await page.goto(BASE_URL);
    await page.waitForTimeout(2000);

    const searchInput = page.locator('input[placeholder*="请输入网关名称"]');
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill(gatewayName || '');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1500);
    }

    const found = await page.locator(`text=${gatewayName}`).isVisible().catch(() => false);
    if (found) {
      console.log('[teardown] WARNING: Gateway still visible after deletion');
    } else {
      console.log('[teardown] Gateway successfully removed from home page');
    }
  } catch (err) {
    console.log(`[teardown] Error during cleanup: ${err.message}`);
  } finally {
    await browser.close();

    // Clean up state files
    try { fs.unlinkSync(ENV_FILE); } catch {}
    try { fs.unlinkSync(STORAGE_FILE); } catch {}
  }
};
