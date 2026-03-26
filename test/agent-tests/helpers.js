/**
 * Agent-Test Helpers — Reusable browser interaction patterns.
 *
 * Usage: The agent-test skill reads this file and injects its content
 * at the top of browser_run_code calls, giving test code access to `H.*` methods.
 *
 * Example browser_run_code with helpers:
 *   async (page) => {
 *     // --- helpers injected here ---
 *     const H = { ... };
 *     // --- test code ---
 *     await H.dropdown(page, '.my-select', 'Option A');
 *   }
 */

const H = {
  // ─── Dropdown / Select ───────────────────────────────────────────
  /**
   * Open a BkSelect dropdown and choose an option by text.
   * Presses Escape first to close any overlapping dropdown.
   */
  async dropdown(page, selector, optionText) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);
    await page.locator(selector).click({ force: true });
    await page.waitForTimeout(300);
    await page.locator('.bk-select-option').filter({ hasText: optionText }).click();
    await page.waitForTimeout(800);
  },

  /**
   * Open a dropdown by nth index of input[placeholder="请选择"] and pick an option.
   * Useful for resource create page where 5 selects share the same placeholder.
   */
  async dropdownNth(page, nthIndex, optionText) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(100);
    await page.locator('input[placeholder="请选择"]').nth(nthIndex).click({ force: true });
    await page.waitForTimeout(300);
    await page.locator('li').filter({ hasText: optionText }).last().click();
    await page.waitForTimeout(800);
  },

  // ─── Form Inputs ─────────────────────────────────────────────────
  /**
   * Fill an input and trigger blur (for validation).
   */
  async fillAndBlur(page, selector, value) {
    const el = page.locator(selector);
    await el.fill(value);
    await el.blur();
    await page.waitForTimeout(300);
  },

  /**
   * Trigger empty-field validation: fill → clear → blur.
   * Required because BkUI won't trigger "请填写" on a never-touched empty field.
   */
  async triggerEmptyValidation(page, selector) {
    const el = page.locator(selector);
    await el.fill('a');
    await el.fill('');
    await el.blur();
    await page.waitForTimeout(300);
  },

  // ─── Sideslider ──────────────────────────────────────────────────
  /**
   * Close a BkSideslider. Handles the "are you sure?" confirmation dialog.
   */
  async closeSlider(page) {
    const closer = page.locator('.bk-sideslider-close').first();
    if (await closer.isVisible({ timeout: 500 }).catch(() => false)) {
      await closer.click({ force: true });
      await page.waitForTimeout(300);
    }
    const confirmBtn = page.locator('.bk-infobox button')
      .filter({ hasText: /确定|确认|离开/ }).first();
    if (await confirmBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await confirmBtn.click({ force: true });
      await page.waitForTimeout(300);
    }
  },

  // ─── Verification Helpers ────────────────────────────────────────
  /**
   * Get the first visible form error text, or null if none.
   */
  async getFormError(page, selector = '.bk-form-error') {
    const el = page.locator(selector).first();
    if (await el.isVisible({ timeout: 500 }).catch(() => false)) {
      return await el.textContent();
    }
    return null;
  },

  /**
   * Check if a toast message appeared with expected text.
   */
  async checkToast(page, expectedText, timeout = 3000) {
    try {
      const msg = page.locator('.bk-message');
      await msg.waitFor({ timeout });
      const text = await msg.textContent();
      return text?.includes(expectedText) ?? false;
    } catch {
      return false;
    }
  },

  /**
   * Count visible table rows.
   */
  async tableRowCount(page, tableSelector = '.bk-table-row') {
    return await page.locator(tableSelector).count();
  },

  /**
   * Check if an element is visible (returns boolean, never throws).
   */
  async isVisible(page, selector, timeout = 500) {
    return await page.locator(selector).first()
      .isVisible({ timeout }).catch(() => false);
  },

  /**
   * Get text content of an element (returns string or null, never throws).
   */
  async getText(page, selector) {
    return await page.locator(selector).first()
      .textContent().catch(() => null);
  },

  // ─── Navigation / Session ────────────────────────────────────────
  /**
   * Navigate and wait for page load.
   */
  async navigateTo(page, baseUrl, path) {
    await page.goto(baseUrl + path);
    await page.waitForTimeout(1500);
  },

  /**
   * Check if session has expired (redirected to login page).
   */
  isLoginPage(page) {
    return page.url().includes('/login/');
  },

  /**
   * Re-authenticate after session expiry.
   * Returns true on success, false on failure.
   */
  async reAuth(page, baseUrl, username, password) {
    await page.goto(baseUrl);
    await page.waitForTimeout(3000);
    if (!page.url().includes('/login/')) return true;

    const hasIdUser = await page.locator('#user').isVisible().catch(() => false);
    if (hasIdUser) {
      await page.locator('#user').click();
      await page.locator('#user').type(username);
      await page.locator('#password').click();
      await page.locator('#password').type(password);
      await page.locator('.login-btn').click();
    } else {
      await page.getByRole('textbox', { name: 'Please enter your username' }).fill(username);
      await page.getByRole('textbox', { name: 'Please enter your password' }).fill(password);
      await page.getByRole('button', { name: 'Log in' }).click();
    }
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(500);
      if (!page.url().includes('/login/')) return true;
    }
    return false;
  },

  // ─── Screenshot (failure only) ──────────────────────────────────
  /**
   * Take a failure screenshot. Returns the path or null on error.
   */
  async failScreenshot(page, caseName, reportDir) {
    const path = `${reportDir}/screenshots/${caseName}.png`;
    try {
      await page.screenshot({ path });
      return path;
    } catch {
      return null;
    }
  },

  // ─── Plugin Wizard ───────────────────────────────────────────────
  /**
   * Add a plugin via the 2-step wizard.
   * Step 1: select plugin card by name, click 下一步.
   * Step 2: click 确定 (use defaults).
   */
  async addPlugin(page, pluginName) {
    // May need to scroll to find the plugin card
    const card = page.locator('.plugin-card, .bk-card').filter({ hasText: pluginName });
    await card.scrollIntoViewIfNeeded();
    await card.click();
    await page.waitForTimeout(300);
    await page.locator('button').filter({ hasText: '下一步' }).click();
    await page.waitForTimeout(500);
    await page.locator('button').filter({ hasText: '确定' }).click();
    await page.waitForTimeout(800);
  },

  // ─── Page Element Extraction (for generate mode) ────────────────
  /**
   * Extract interactive elements from the current page.
   * Returns a compact summary instead of the full accessibility tree.
   * This replaces browser_snapshot in generate mode, saving 20-90k tokens.
   */
  async extractPageElements(page) {
    return await page.evaluate(() => {
      const extract = (sel) => Array.from(document.querySelectorAll(sel))
        .filter(el => el.offsetParent !== null)
        .map(el => ({
          tag: el.tagName.toLowerCase(),
          text: el.textContent?.trim()?.slice(0, 50) || '',
          type: el.getAttribute('type') || '',
          placeholder: el.getAttribute('placeholder') || '',
          class: el.className?.toString()?.slice(0, 80) || '',
          role: el.getAttribute('role') || '',
          id: el.id || '',
          name: el.getAttribute('name') || '',
          ariaLabel: el.getAttribute('aria-label') || '',
        }));

      return {
        buttons: extract('button:not([style*="display: none"])'),
        inputs: extract('input:not([type="hidden"])'),
        selects: extract('select, [role="combobox"], .bk-select'),
        links: extract('a[href]').map(l => ({
          ...l,
          href: document.querySelector(`a[href]`)?.getAttribute('href') || ''
        })),
        textareas: extract('textarea'),
        tables: extract('table, .bk-table').map(t => ({
          ...t,
          rows: t.tag === 'table'
            ? document.querySelectorAll(`#${t.id || ''} tbody tr`).length
            : 0
        })),
        tabs: extract('[role="tab"]'),
        headings: extract('h1, h2, h3, h4'),
        switches: extract('.bk-switcher'),
        dialogs: extract('[role="dialog"], .bk-dialog, .bk-sideslider'),
      };
    });
  }
};
