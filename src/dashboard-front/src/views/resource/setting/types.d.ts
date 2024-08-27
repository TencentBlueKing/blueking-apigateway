type TRequestMethod = 'ANY' | 'DELETE' | 'GET' | 'PATCH' | 'POST' | 'PUT';
type ActionType = 'add' | 'update';

interface IAuthConfig {
  auth_verified_required: boolean;
  app_verified_required: boolean;
  resource_perm_required: boolean;
}

interface IBackendConfig {
  method: TRequestMethod;
  path: string;
  match_subpath: boolean;
  timeout: number;
}

interface IBackend {
  name: string;
  config: IBackendConfig;
  path?: string;
}

interface IPluginConfig {
  name?: string;
  type: string;
  yaml: string;
}

interface IPublicConfig {
  is_public: boolean;
  allow_apply_permission: boolean;
}

interface IDoc {
  id?: number;
  language?: 'zh' | 'en';
}

interface IImportedResource {
  allow_apply_permission: boolean;
  auth_config?: IAuthConfig;
  backend?: IBackend;
  description?: string | null;
  description_en?: string | null;
  doc: IDoc[] | null;
  id: number | null;
  is_public: boolean;
  label_ids?: number[];
  labels: any[] | null;
  match_subpath: boolean;
  method: TRequestMethod;
  name: string;
  openapi_schema: Record<string, any>;
  path: string;
  plugin_configs?: IPluginConfig[] | null;
}

interface ILocalImportedResource extends Partial<IImportedResource> {
  _localId: number;
  _unchecked: boolean;
}

export {
  ActionType,
  IBackend,
  IBackendConfig,
  IAuthConfig,
  IPluginConfig,
  IPublicConfig,
  IImportedResource,
  ILocalImportedResource,
};
