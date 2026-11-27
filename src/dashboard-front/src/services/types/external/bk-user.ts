// 蓝鲸用户管理多租户人员查询
export interface ITenantUsersQuery {
  keyword: string
}

// 蓝鲸用户管理语言设置
export interface IUserLanguageInput {
  language: string
}

// 蓝鲸用户管理多租户人员查询
export interface ITenantUserOutput {
  bk_username: string
  display_name: string
}
