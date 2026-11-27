export interface IGatewayMemberUpdateInputSLZ {
  role: GatewayMemberRole
}

export interface IGatewayMemberCreateInputSLZ {
  username: string
  role: GatewayMemberRole
}

export type GatewayMemberRole = 'administrator' | 'operator';

export interface IGatewayMemberOutput {
  id: number
  username: string
  role: GatewayMemberRole
}

export interface IGatewayMemberBatchCreateOutput {
  created: IGatewayMemberOutput[]
  skipped: IGatewayMemberOutput[]
}

// GET /gateways/{gateway_id}/me/role/
export interface IGatewayUserRoleOutput {
  role: GatewayMemberRole
}
