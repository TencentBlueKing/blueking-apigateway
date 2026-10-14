const { test, expect } = require('@playwright/test');
const {
  getActiveSideslider, selectDropdownOption, closeSlider,
  getAvailablePluginSelectionOption, openFirstResourcePluginPanel,
  clickConfirm,
} = require('../helpers');

test('a visible drawer body is usable when its fixed-position parent has zero height', async ({ page }) => {
  await page.setContent('<div class="bk-sideslider" style="height:0"><div class="bk-modal-wrapper" style="position:fixed;top:0;right:0;width:300px;height:300px"><button>Save</button><button class="bk-sideslider-close" onclick="this.closest(\'.bk-sideslider\').remove()">Close</button></div></div>');
  await expect(getActiveSideslider(page)).toBeVisible();
  await expect(getActiveSideslider(page).getByRole('button', { name: 'Save' })).toBeVisible();
  await closeSlider(page);
  await expect(getActiveSideslider(page)).toHaveCount(0);
});

test('selection waits for the rendered option and ignores a hidden duplicate', async ({ page }) => {
  await page.setContent(`<div style="display:none"><div class="bk-select-option">default</div></div>
    <button style="margin:100px" onclick="setTimeout(() => document.querySelector('#options').style.display='block', 600)">Choose</button>
    <div id="options" style="display:none"><div class="bk-select-option" onclick="window.selected='default'">default</div></div>`);
  expect(await selectDropdownOption(page, page.getByRole('button', { name: 'Choose' }), 'default')).toBe(true);
  expect(await page.evaluate(() => window.selected)).toBe('default');
});

test('a hidden added label does not exclude an available plugin', async ({ page }) => {
  await page.setContent('<div class="plugin-list"><div class="plugin"><span class="bindding-text" style="display:none">已添加</span><p class="plugin-name">CORS</p></div><div class="plugin disabled"><span class="bindding-text">已添加</span><p class="plugin-name">Used</p></div></div>');
  await expect(getAvailablePluginSelectionOption(page, 'CORS')).toBeVisible();
  await expect(getAvailablePluginSelectionOption(page, 'Used')).toHaveCount(0);
});

test('the resource plugin count button opens the panel', async ({ page }) => {
  await page.setContent('<table><tbody><tr><td><button onclick="window.opened=true">0 </button></td></tr></tbody></table>');
  expect(await openFirstResourcePluginPanel(page)).toBe(true);
  expect(await page.evaluate(() => window.opened)).toBe(true);
});

test('confirmation waits for the dialog after asynchronous delete preparation', async ({ page }) => {
  await page.setContent('<main>Resource</main>');
  await page.evaluate(() => {
    setTimeout(() => {
      document.body.insertAdjacentHTML('beforeend', '<div class="bk-modal-wrapper"><button onclick="window.confirmed=true">确定</button></div>');
    }, 500);
  });
  expect(await clickConfirm(page)).toBe(true);
  expect(await page.evaluate(() => window.confirmed)).toBe(true);
});

test('plugin choice matches the title rather than another plugin description', async ({ page }) => {
  await page.setContent('<div class="plugin-list"><div class="plugin"><p class="plugin-name">Token</p><div>Header 转换说明</div></div><div class="plugin"><p class="plugin-name">Header 转换</p></div></div>');
  await expect(getAvailablePluginSelectionOption(page, /Header.*转换/).locator('.plugin-name')).toHaveText('Header 转换');
});
