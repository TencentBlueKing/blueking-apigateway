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
