export interface BasicInfoParams {
  name?: string // 名称
  id?: number // 可选，ID
  url?: string // 可选，URL
  description?: string // 可选，描述
  description_en?: string // 可选，英文描述
  public_key_fingerprint?: string // 可选，公钥指纹
  bk_app_codes?: string // 蓝鲸应用代码
  related_app_codes?: string[] // 相关应用代码[]
  docs_url?: string // 文档URL
  api_domain?: string // 可选，API域名
  developers?: string[] // 可选，开发者列表
  maintainers?: string[] // 可选，维护者列表
  status?: number // 可选，状态
  is_public?: boolean // 可选，是否公开
  created_by?: string // 创建者
  created_time?: string // 创建时间
  public_key?: string // 公钥
  is_official?: boolean // 是否官方
  publish_validate_msg?: string // 可选，发布验证消息
  kind?: number // 可选，类型
  links?: { // 可选，链接
    [key: string]: any // 键值对，键为字符串，值为任意类型
  }
  extra_info?: { // 可选，额外信息
    [key: string]: string // 键值对，键和值均为字符串
  }
  programmable_gateway_git_info?: { // 可选，可编程网关Git信息
    [key: string]: string // 键值对，键和值均为字符串
  }
  doc_maintainers?: { // 可选，文档维护者
    type: string // 类型
    contacts?: string[] // 可选，联系人列表
    service_account?: { // 可选，服务账号
      name: string // 名称
      link: string // 链接
    }
  }
  tenant_mode?: string
  tenant_id?: string
}

export interface DialogParams {
  isShow: boolean // 是否显示
  loading: boolean // 是否加载中
  title?: string // 可选，标题
}
