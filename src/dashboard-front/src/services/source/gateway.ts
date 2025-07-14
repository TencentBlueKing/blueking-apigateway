import http from '../http';

const path = '/gateways';

interface IStage {
  id: number
  name: string
  released: boolean
}

interface IApiGateway {
  id: number
  name: string
  description: string
  description_en?: string
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

interface IApiGatewayDetail extends IApiGateway {
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

interface IApiGatewayEditParam {
  // 名称
  name: string
  // ID
  id: number
  // URL
  url: string
  // 描述
  description: string
  // 英文描述
  description_en: string
  // 公钥指纹
  public_key_fingerprint: string
  // 蓝鲸应用代码
  bk_app_codes: string[]
  // 相关应用代码[]
  related_app_codes: string[]
  // 文档URL
  docs_url: string
  // API域名
  api_domain: string
  // 开发者列表
  developers: string[]
  // 维护者列表
  maintainers: string[]
  // 状态
  status: number
  // 是否公开
  is_public: boolean
  // 创建者
  created_by: string
  // 创建时间
  created_time: string
  // 公钥
  public_key: string
  // 是否官方
  is_official: boolean
  // 发布验证消息
  publish_validate_msg: string
  // 类型
  kind: number
  // 链接
  links: { [key: string]: any }
  // 额外信息
  extra_info: { [key: string]: string }
  // 可编程网关Git信息
  programmable_gateway_git_info: { [key: string]: string }
  // 文档维护者
  doc_maintainers: {
    // 类型
    type: string
    // 联系人列表
    contacts: string[]
    // 服务账号
    service_account: {
      // 名称
      name: string
      // 链接
      link: string
    }
  }
  tenant_mode: string
  tenant_id: string
}

export function getGatewayList(params: {
  limit?: number
  offset?: number
} = {}) {
  return http.get<{
    count: number
    results: IApiGateway[]
  }>(`${path}/`, params);
}

export function getGatewayDetail(id: number) {
  return http.get<IApiGatewayDetail>(`${path}/${id}/`);
}

// 新建网关
export const createGateway = (param: Partial<IApiGatewayEditParam>) => http.post(`${path}/`, param);

export const deleteGateway = (id: number) => http.delete(`${path}/${id}/`);

export const patchGateway = (id: number, data: Partial<IApiGatewayEditParam>) => http.patch(`${path}/${id}/`, data);

export const putGatewayBasics = (id: number, data: Partial<IApiGatewayEditParam>) => http.put(`${path}/${id}/`, data);

// 获取操作指引
export const getGuideDocs = (id: number) => http.get(`${path}/${id}/dev-guideline/`);

export const toggleStatus = (id: number, data: { status: number }) => http.put(`${path}/${id}/status/`, data);
