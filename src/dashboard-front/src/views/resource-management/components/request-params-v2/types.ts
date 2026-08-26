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

export const JSON_SCHEMA_TYPES = [
  'string',
  'number',
  'integer',
  'boolean',
  'object',
  'array',
  'null',
] as const;

export const PARAMETER_LOCATIONS = [
  'header',
  'query',
  'path',
] as const;

export const SCALAR_PARAMETER_TYPES = [
  'string',
  'number',
  'boolean',
] as const;

export const BODY_PARAMETER_TYPES = [
  ...SCALAR_PARAMETER_TYPES,
  'array',
  'object',
] as const;

export const JSON_SCHEMA_STRING_FORMATS = [
  'date-time',
  'date',
  'time',
  'email',
  'hostname',
  'ipv4',
  'ipv6',
  'uri',
  'uuid',
  'binary',
] as const;

export interface IJsonSchemaObject {
  [key: string]: unknown
  $id?: string
  $ref?: string
  $schema?: string
  additionalProperties?: boolean | JsonSchema
  const?: unknown
  default?: unknown
  deprecated?: boolean
  description?: string
  enum?: unknown[]
  examples?: unknown[]
  exclusiveMaximum?: boolean | number
  exclusiveMinimum?: boolean | number
  format?: string
  items?: JsonSchema | JsonSchema[]
  maxItems?: number
  maxLength?: number
  maxProperties?: number
  maximum?: number
  minItems?: number
  minLength?: number
  minProperties?: number
  minimum?: number
  multipleOf?: number
  pattern?: string
  properties?: Record<string, JsonSchema>
  readOnly?: boolean
  required?: string[]
  title?: string
  type?: JsonSchemaType | JsonSchemaType[]
  uniqueItems?: boolean
  writeOnly?: boolean
}

export type JsonSchema = boolean | IJsonSchemaObject;

export type JsonSchemaType = typeof JSON_SCHEMA_TYPES[number];
export type ParameterLocation = typeof PARAMETER_LOCATIONS[number];
export type ScalarParameterType = typeof SCALAR_PARAMETER_TYPES[number];
export type BodyParameterType = typeof BODY_PARAMETER_TYPES[number];

export interface IRequestFieldRow {
  children?: IRequestFieldRow[]
  description: string
  id: string
  name: string
  options: IJsonSchemaObject
  required: boolean
  type: BodyParameterType
}

export interface IRequestParameterRow {
  description: string
  id: string
  in: ParameterLocation
  name: string
  options: IJsonSchemaObject
  required: boolean
  type: ScalarParameterType
}

export interface IRequestBodyState {
  mediaType: string
  required: boolean
  root: IRequestFieldRow
}

export interface IRequestParamsState {
  body?: IRequestBodyState
  parameters: Record<ParameterLocation, IRequestParameterRow[]>
}

export interface IOpenApiParameter {
  description?: string
  in: string
  name: string
  required?: boolean
  schema?: IJsonSchemaObject
  type?: string
  [key: string]: unknown
}

export interface IOpenApiRequestBody {
  content: Record<string, { schema?: JsonSchema }>
  description?: string
  required?: boolean
  [key: string]: unknown
}

export interface IOpenApiOperationSchema {
  parameters?: IOpenApiParameter[]
  requestBody?: IOpenApiRequestBody
  [key: string]: unknown
}

export interface IRequestParamsDetail {
  openapi_schema?: IOpenApiOperationSchema
  schema?: IOpenApiOperationSchema
}

export interface IRequestParamsValue {
  parameters: IOpenApiParameter[]
  requestBody: IOpenApiRequestBody | null
}

export interface IFlatRequestFieldRow {
  depth: number
  isArrayItem: boolean
  isRoot: boolean
  parent?: IRequestFieldRow
  path: string
  row: IRequestFieldRow
}
