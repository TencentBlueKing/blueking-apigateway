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
