// @generated from: test-bdd/cases/05-环境概览/02-环境生命周期.md
// @generated-date: 2026-06-04

const { test, expect } = require('@playwright/test');
const {
  createTestIdentifier,
  createTestStage,
  updateTestStage,
  cleanupStagesByName,
  getGatewayId,
  listStages,
  navigateToGatewayPage,
  pageApiPut,
} = require('../../runtime/helpers');

test.describe('功能: 环境概览 - 环境生命周期', () => {
  test('场景: 管理环境本体生命周期', async ({ page }) => {
    const gatewayId = getGatewayId();
    const stageName = createTestIdentifier('bdd_stage_life', { maxLength: 20 });
    const updatedDescription = `BDD updated stage ${stageName}`;
    let stage;

    await navigateToGatewayPage(page, gatewayId, '环境概览', '/stage/overview');
    await expect(page).toHaveURL(new RegExp(`/${gatewayId}/stage/overview`));

    try {
      stage = await createTestStage(page, gatewayId, {
        name: stageName,
        description: `BDD stage ${stageName}`,
      });

      let stages = await listStages(page, gatewayId);
      let created = stages.find(item => item.name === stageName);
      expect(created).toBeTruthy();
      expect(created.description).toContain(stageName);

      await updateTestStage(page, gatewayId, stage.id, {
        description: updatedDescription,
        host: 'example.com',
      });

      stages = await listStages(page, gatewayId);
      const updated = stages.find(item => item.name === stageName);
      expect(updated).toBeTruthy();
      expect(updated.description).toBe(updatedDescription);

      await pageApiPut(page, `/gateways/${gatewayId}/stages/${stage.id}/status/`, { status: 0 });
      stages = await listStages(page, gatewayId);
      const inactive = stages.find(item => item.name === stageName);
      expect(inactive).toBeTruthy();
      expect(Number(inactive.status)).toBe(0);

      await cleanupStagesByName(page, gatewayId, stageName);
      stage = null;

      stages = await listStages(page, gatewayId);
      expect(stages.some(item => item.name === stageName)).toBe(false);
    } finally {
      if (stage) {
        await cleanupStagesByName(page, gatewayId, stageName);
      }
    }
  });
});
