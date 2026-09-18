/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

import type {
  BodyParameterType,
  IJsonSchemaObject,
  JsonSchema,
} from '../request-params-v2/types';

export {
  BODY_PARAMETER_TYPES,
} from '../request-params-v2/types';

export type {
  BodyParameterType,
  IJsonSchemaObject,
  JsonSchema,
};

export interface IResponseFieldRow {
  children?: IResponseFieldRow[]
  description: string
  id: string
  name: string
  options: IJsonSchemaObject
  type: BodyParameterType
}

export interface IOpenApiResponse {
  [key: string]: unknown
  content?: Record<string, {
    schema?: JsonSchema
    [key: string]: unknown
  }>
  description: string
}

export interface IOpenApiOperationSchema {
  [key: string]: unknown
  responses?: Record<string, IOpenApiResponse>
}

export interface IResponseParamsDetail {
  openapi_schema?: IOpenApiOperationSchema
  schema?: IOpenApiOperationSchema
}

export interface IResponseState {
  code: string
  expanded: boolean
  id: string
  root: IResponseFieldRow
}

export interface IFlatResponseFieldRow {
  depth: number
  isArrayItem: boolean
  isRoot: boolean
  parent?: IResponseFieldRow
  path: string
  row: IResponseFieldRow
}

export type IResponseParamsValue = Record<string, IOpenApiResponse>;
