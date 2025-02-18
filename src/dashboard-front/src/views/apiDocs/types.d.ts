type TabType = 'gateway' | 'component';
type LanguageType = 'python' | 'java' | 'golang';

interface INavItem {
  id: string;
  name: string;
}

// 网关类型

interface IApiGatewayBasics {
  id: number;
  name: string;
  description: string;
  maintainers: string[];
  is_official: boolean;
  api_url: string;
  sdks?: IApiGatewaySdk[];
  tenant_mode?: string;
  tenant_id?: string;
}

interface IApiGatewaySdkDoc {
  language: LanguageType;
  resource_version: IResourceVersion;
  sdk: IApiGatewaySdk;
  stage: { id: number, name: string }
}

interface IApiGatewaySdk {
  language: LanguageType;
  name: string;
  version: string;
  url: string;
  install_command: string;
}

interface IResourceVersion {
  id: number;
  version: string;
}

interface IResource {
  id: number;
  name: string;
  description: string;
  method: string;
  path: string;
  verified_user_required: boolean;
  verified_app_required: boolean;
  resource_perm_required: boolean;
  allow_apply_permission: boolean;
  labels: { id: number, name: string }[];
}

interface IStage {
  id: number;
  name: string;
  description: string;
}

// 组件类型

interface IBoard {
  board: string;
  board_label: string;
  categories: ICategory[];
  sdk?: IComponentSdk;
}

interface ICategory {
  id: string;
  name: string;
  systems: ISystem[];
  _navId?: string;
}

interface ISystem {
  name: string;
  description: string;
}

interface ISystemBasics {
  name: string;
  description: string;
  comment: string;
  maintainers: string[];
}

interface IComponent {
  id: number;
  name: string;
  description: string;
  verified_app_required: boolean;
  verified_user_required: boolean;
  component_permission_required: boolean;
}

interface IComponentSdk {
  board_label: string;
  sdk_name: string;
  sdk_description: string;
  sdk_version_number: string;
  sdk_download_url: string;
  sdk_install_command: string;
  language: LanguageType;
}

// 其他

interface ISdk extends Partial<IApiGatewaySdk>, Partial<IComponentSdk> {
}

export {
  IApiGatewayBasics,
  IApiGatewaySdk,
  IApiGatewaySdkDoc,
  IBoard,
  ICategory,
  IComponent,
  IComponentSdk,
  INavItem,
  IResource,
  IResourceVersion,
  ISdk,
  IStage,
  ISystem,
  ISystemBasics,
  LanguageType,
  TabType,
};
