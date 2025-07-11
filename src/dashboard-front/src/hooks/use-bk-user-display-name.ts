/**
 * @description 配置 BkUserDisplayName 组件
 * @param {string} tenantId 要覆盖的租户 id
 */
import BkUserDisplayName from '@blueking/bk-user-display-name';
import { useFeatureFlag, useUserInfo } from '@/stores';

export function useBkUserDisplayName() {
  const userStore = useUserInfo();
  const featureFlagStore = useFeatureFlag();

  return {
    configure: (tenantId?: string) => BkUserDisplayName.configure({
      tenantId: tenantId || userStore.info.tenant_id || '',
      apiBaseUrl: featureFlagStore.apiBaseUrl,
    }),
  };
}
