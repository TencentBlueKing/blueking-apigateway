import type { GatewayMemberRole } from '@/services/types/responses/gateway-members';

export interface IGatewayMemberCreateInputSLZ {
  username: string
  role: GatewayMemberRole
}
