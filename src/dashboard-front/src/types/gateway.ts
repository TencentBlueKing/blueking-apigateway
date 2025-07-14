/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
export interface ServiceAccount {
  // 服务账号名称
  name: string
  // 服务账号链接
  link: string
}

export interface DocMaintainers {
  // 文档维护者类型
  type: string
  // 文档维护者联系方式列表
  contacts: string[]
  // 关联的服务账号
  service_account: ServiceAccount
}

export interface Gateway {
  // 网关ID
  id: number
  // 网关名称
  name: string
  // 网关描述
  description: string
  // 网关维护者列表
  maintainers: string[]
  // 文档维护者信息
  doc_maintainers: DocMaintainers
  // 开发者列表
  developers: any[]
  // 网关状态
  status: number
  // 是否为可编程网关，0 非可编程网关，1 可编程网关
  kind: 0 | 1
  // 是否公开
  is_public: boolean
  // 创建者
  created_by: string
  // 创建时间
  created_time: string
  // 更新时间
  updated_time: string
  // 公钥
  public_key: string
  // 是否为官方网关
  is_official: boolean
  // 是否允许更新网关认证
  allow_update_gateway_auth: boolean
  // API域名
  api_domain: string
  // 文档URL
  docs_url: string
  // 公钥指纹
  public_key_fingerprint: string
  // 蓝鲸应用代码列表
  bk_app_codes: any[]
  // 相关应用代码列表
  related_app_codes: any[]
  // 额外信息
  extra_info: Record<string, any>
  // 链接信息
  links: Record<string, any>
}

export interface GatewayListItem {
  // 创建者
  created_by: string
  // 创建时间
  created_time: string
  // 描述
  description: string
  // 额外信息
  extra_info: Record<string, any>
  // 网关ID
  id: number
  // 是否为官方网关
  is_official: boolean
  // 是否公开
  is_public: boolean
  // 是否为可编程网关，0 非可编程网关，1 可编程网关
  kind: 0 | 1
  // 网关名称
  name: string
  // 资源数量
  resource_count: number
  // 网关状态
  status: number
  // 更新时间
  updated_time: string
  // 阶段列表
  stages: {
    // 阶段ID
    id: number
    // 阶段名称
    name: string
    // 是否已发布
    released: boolean
  }[]
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

export interface IStage {
  id: number
  name: string
  released: boolean
}

// 网关列表参数
export interface IApiGateway {
  id: number
  name: string
  description: string
  tenant_mode: string
  tenant_id: string
  status: number
  kind: number
  is_public: boolean
  is_official: boolean
  resource_count: number
  stages: IStage[]
  extra_info: any
  created_by: string
  created_time: string
  updated_time: string
}

export interface IApiGatewayDetail extends IApiGateway {
  maintainers: []
  doc_maintainers: {
    type: string
    contacts: string[]
    service_account: {
      name: string
      link: string
    }
  }
  developers: string[]
  public_key: string
  allow_update_gateway_auth: boolean
  api_domain: string
  docs_url: string
  public_key_fingerprint: string
  bk_app_codes: string[]
  related_app_codes: string[]
  links: any
}
