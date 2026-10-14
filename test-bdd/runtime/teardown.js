// Delete only the gateway whose exact ID/name was persisted by this run.
const { chromium } = require('@playwright/test');
const fs = require('fs');
const { BASE_URL } = require('./test-env');
const { cleanupRuntimeArtifacts, readRuntimeState, STORAGE_STATE_FILE } = require('./helpers');
const { deleteOwnedGateway } = require('./test-data');

module.exports = async () => {
  const state = readRuntimeState();
  if (!state.TEST_GATEWAY_ID) return;
  const browser = await chromium.launch();
  const context = await browser.newContext(fs.existsSync(STORAGE_STATE_FILE)
    ? { storageState: STORAGE_STATE_FILE } : {});
  const page = await context.newPage();
  try {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    // API helpers reauthenticate on 401. A frontend 503 must not prevent
    // cleanup while the authenticated backend API is still healthy.
    await deleteOwnedGateway(page, { id: state.TEST_GATEWAY_ID, name: state.TEST_GATEWAY_NAME });
    cleanupRuntimeArtifacts();
    console.log(`[teardown] Verified deletion: ${state.TEST_GATEWAY_NAME} (${state.TEST_GATEWAY_ID})`);
  } finally {
    // Keep ownership state on failure so cleanup can be retried honestly.
    await browser.close();
  }
};
