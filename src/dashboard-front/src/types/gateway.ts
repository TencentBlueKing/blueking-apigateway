export interface ServiceAccount {
  name: string;
  link: string;
}

export interface DocMaintainers {
  type: string;
  contacts: string[];
  service_account: ServiceAccount;
}

export interface Gateway {
  id: number;
  name: string;
  description: string;
  maintainers: string[];
  doc_maintainers: DocMaintainers;
  developers: any[];
  status: number;
  // 是否为可编程网关，0 非可编程网关，1 可编程网关
  kind: 0 | 1;
  is_public: boolean;
  created_by: string;
  created_time: string;
  updated_time: string;
  public_key: string;
  is_official: boolean;
  allow_update_gateway_auth: boolean;
  api_domain: string;
  docs_url: string;
  public_key_fingerprint: string;
  bk_app_codes: any[];
  related_app_codes: any[];
  extra_info: any;
  links: any;
}

export interface GatewayListItem {
  created_by: string;
  created_time: string;
  description: string;
  extra_info: any;
  id: number;
  is_official: boolean;
  is_public: boolean;
  // 是否为可编程网关，0 非可编程网关，1 可编程网关
  kind: 0 | 1;
  name: string;
  resource_count: number;
  status: number;
  updated_time: string;
  stages: {
    id: number;
    name: string;
    released: boolean;
  }[];
}


