/**
 * @description 配置 BkUserDisplayName 组件
 * @param {string} tenantId 要覆盖的租户 id
 */
import BkUserDisplayName from '@blueking/bk-user-display-name';
import { useUser } from '@/store';

export function useBkUserDisplayName() {
  const userStore = useUser();

  return {
    configure: (tenantId?: string) => BkUserDisplayName.configure({
      tenantId: tenantId || userStore.user.tenant_id,
      apiBaseUrl: userStore.apiBaseUrl,
    }),
  };
}
