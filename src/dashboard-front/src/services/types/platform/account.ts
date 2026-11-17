// GET /accounts/userinfo/
export interface IUserInfoOutput {
  avatar_url: string
  chinese_name: string
  display_name: string
  tenant_id: string | null
  username: string
  time_zone: string
}
