// @generated from: test-bdd/cases/27-告警策略/01-告警策略管理.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  createAlarmStrategy,
  cleanupAlarmStrategiesByName,
  createTestName,
  getGatewayId,
  navigateToGatewayPage,
  pageApiDelete,
  pageApiGet,
  pageApiPatch,
  pageApiPut,
  unwrapApiResults,
} = require('../../runtime/helpers');

async function listStrategies(page, gatewayId) {
  return unwrapApiResults(await pageApiGet(page, `/gateways/${gatewayId}/monitors/alarm/strategies/`));
}

test.describe('功能: 告警策略 - 告警策略管理', () => {
  test.setTimeout(120000);

  test('场景: 管理告警策略生命周期', async ({ page }) => {
    const gatewayId = getGatewayId();
    const strategyName = createTestName('bdd-alarm-life');
    const updatedName = createTestName('bdd-alarm-edit');
    let cleanupNames = [strategyName, updatedName];
    let strategy;

    await navigateToGatewayPage(page, gatewayId, '告警策略', '/monitor/alarm-strategy');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/monitor/alarm-strategy`));

    try {
      strategy = await createAlarmStrategy(page, gatewayId, { name: strategyName });
      let strategies = await listStrategies(page, gatewayId);
      let current = strategies.find(item => item.name === strategyName);
      expect(current).toBeTruthy();

      await pageApiPut(page, `/gateways/${gatewayId}/monitors/alarm/strategies/${strategy.id}/`, {
        name: updatedName,
        alarm_type: 'resource_backend',
        alarm_subtype: 'status_code_5xx',
        gateway_label_ids: [],
        effective_stages: [],
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
      });

      strategies = await listStrategies(page, gatewayId);
      current = strategies.find(item => item.name === updatedName);
      expect(current).toBeTruthy();

      await pageApiPatch(page, `/gateways/${gatewayId}/monitors/alarm/strategies/${strategy.id}/status/`, { enabled: false });
      strategies = await listStrategies(page, gatewayId);
      current = strategies.find(item => item.id === strategy.id);
      expect(current).toBeTruthy();
      expect(Boolean(current.enabled)).toBe(false);

      await pageApiPatch(page, `/gateways/${gatewayId}/monitors/alarm/strategies/${strategy.id}/status/`, { enabled: true });
      strategies = await listStrategies(page, gatewayId);
      current = strategies.find(item => item.id === strategy.id);
      expect(current).toBeTruthy();
      expect(Boolean(current.enabled)).toBe(true);

      await pageApiDelete(page, `/gateways/${gatewayId}/monitors/alarm/strategies/${strategy.id}/`);
      strategy = null;

      strategies = await listStrategies(page, gatewayId);
      expect(strategies.some(item => cleanupNames.includes(item.name))).toBe(false);
    } finally {
      if (strategy) {
        await cleanupAlarmStrategiesByName(page, gatewayId, cleanupNames);
      }
    }
  });
});
