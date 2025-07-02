export interface ServiceAccount {
  name: string; // 服务账号名称
  link: string; // 服务账号链接
}

export interface DocMaintainers {
  type: string; // 文档维护者类型
  contacts: string[]; // 文档维护者联系方式列表
  service_account: ServiceAccount; // 关联的服务账号
}

export interface Gateway {
  id: number; // 网关ID
  name: string; // 网关名称
  description: string; // 网关描述
  maintainers: string[]; // 网关维护者列表
  doc_maintainers: DocMaintainers; // 文档维护者信息
  developers: any[]; // 开发者列表
  status: number; // 网关状态
  kind: 0 | 1; // 是否为可编程网关，0 非可编程网关，1 可编程网关
  is_public: boolean; // 是否公开
  created_by: string; // 创建者
  created_time: string; // 创建时间
  updated_time: string; // 更新时间
  public_key: string; // 公钥
  is_official: boolean; // 是否为官方网关
  allow_update_gateway_auth: boolean; // 是否允许更新网关认证
  api_domain: string; // API域名
  docs_url: string; // 文档URL
  public_key_fingerprint: string; // 公钥指纹
  bk_app_codes: any[]; // 蓝鲸应用代码列表
  related_app_codes: any[]; // 相关应用代码列表
  extra_info: any; // 额外信息
  links: any; // 链接信息
}

export interface GatewayListItem {
  created_by: string; // 创建者
  created_time: string; // 创建时间
  description: string; // 描述
  extra_info: any; // 额外信息
  id: number; // 网关ID
  is_official: boolean; // 是否为官方网关
  is_public: boolean; // 是否公开
  kind: 0 | 1; // 是否为可编程网关，0 非可编程网关，1 可编程网关
  name: string; // 网关名称
  resource_count: number; // 资源数量
  status: number; // 网关状态
  updated_time: string; // 更新时间
  stages: {
    id: number; // 阶段ID
    name: string; // 阶段名称
    released: boolean; // 是否已发布
  }[]; // 阶段列表
}

// 导出参数interface
export interface IExportParams {
  export_type?: string
  query?: string
  method?: string
  label_name?: string
  file_type?: string
  resource_ids?: Array<number>
  resource_filter_condition?: any
}
