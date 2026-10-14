const { test } = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { attachHardFailureGuard, assertNoHardFailure } = require('../helpers');

function pageWithText(text, exceptions = []) {
  const page = new EventEmitter();
  page.locator = selector => ({
    textContent: async () => text,
    evaluateAll: async () => exceptions,
  });
  return page;
}

test('ordinary status-code data is not a fatal error page', async () => {
  await assertNoHardFailure(pageWithText('状态码 200 400 500 请求数 502'), 'status filter');
});

test('an HTTP 500 response fails even when the table renders empty', async () => {
  const page = pageWithText('暂无数据');
  attachHardFailureGuard(page);
  page.emit('response', { url: () => 'https://example.test/backend/logs/', status: () => 500 });
  await assert.rejects(assertNoHardFailure(page), /fatal response: 500/);
});

test('an uncaught browser exception fails even when the page renders', async () => {
  const page = pageWithText('资源配置');
  attachHardFailureGuard(page);
  page.emit('pageerror', new Error('Cannot read properties of undefined'));
  await assert.rejects(assertNoHardFailure(page), /Cannot read properties/);
});

test('the exception component still detects a numeric error page', async () => {
  await assert.rejects(assertNoHardFailure(pageWithText('500', ['500'])), /fatal page content/);
});

test('an explicitly expected validation event is retained as a diagnostic', async () => {
  const page = pageWithText('权限申请已提交');
  const state = attachHardFailureGuard(page, { expectedPageErrors: ['请选择应用'] });
  page.emit('pageerror', new Error('请选择应用'));
  await assertNoHardFailure(page);
  assert.deepEqual(state.diagnostics, ['pageerror: 请选择应用']);
});

test('expected validation does not suppress other exceptions or HTTP failures', async () => {
  const page = pageWithText('权限申请已提交');
  attachHardFailureGuard(page, { expectedPageErrors: ['请选择应用'] });
  page.emit('pageerror', new Error('请选择应用: unexpected suffix'));
  page.emit('response', { url: () => 'https://example.test/backend/permissions/', status: () => 500 });
  await assert.rejects(assertNoHardFailure(page), error => {
    assert.match(error.message, /unexpected suffix/);
    assert.match(error.message, /fatal response: 500/);
    return true;
  });
});
