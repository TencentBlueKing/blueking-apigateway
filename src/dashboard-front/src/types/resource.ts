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

type TRequestMethod = 'ANY' | 'DELETE' | 'GET' | 'PATCH' | 'POST' | 'PUT';
type ActionType = 'add' | 'update';

interface IAuthConfig {
  auth_verified_required: boolean
  app_verified_required: boolean
  resource_perm_required: boolean
}

interface IBackendConfig {
  method: TRequestMethod
  path: string
  match_subpath: boolean
  timeout: number
}

interface IBackend {
  name: string
  config: IBackendConfig
  path?: string
}

interface IPluginConfig {
  name?: string
  type: string
  yaml: string
}

interface IPublicConfig {
  is_public: boolean
  allow_apply_permission: boolean
}

interface IDoc {
  id?: number
  language?: 'zh' | 'en'
}

interface IImportedResource {
  allow_apply_permission: boolean
  auth_config?: IAuthConfig
  backend?: IBackend
  description?: string | null
  description_en?: string | null
  doc: IDoc[] | null
  id: number | null
  is_public: boolean
  label_ids?: number[]
  labels: any[] | null
  match_subpath: boolean
  method: TRequestMethod
  name: string
  openapi_schema: Record<string, any>
  path: string
  plugin_configs?: IPluginConfig[] | null
}

interface ILocalImportedResource extends Partial<IImportedResource> {
  _localId: number
  _unchecked: boolean
}

interface ResourcesItem {
  id: number
  name: string
  description: string
  method: string
  path: string
  created_time: string
  updated_time: string
  backend: {
    id: number
    name: string
  }
  labels: [
    {
      id: number
      name: string
    },
  ]
  docs: Array<unknown>
  has_updated: false
  plugin_count: number
}

export type {
  ActionType,
  IBackend,
  IBackendConfig,
  IAuthConfig,
  IPluginConfig,
  IPublicConfig,
  IImportedResource,
  ILocalImportedResource,
  ResourcesItem,
};
