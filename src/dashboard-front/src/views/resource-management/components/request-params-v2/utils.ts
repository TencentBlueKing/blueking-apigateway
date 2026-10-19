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

import { cloneDeep, uniqueId } from 'lodash-es';

import {
  type BodyParameterType,
  type IFlatRequestFieldRow,
  type IJsonSchemaObject,
  type IOpenApiOperationSchema,
  type IOpenApiParameter,
  type IOpenApiRequestBody,
  type IRequestBodyState,
  type IRequestFieldRow,
  type IRequestParameterRow,
  type IRequestParamsState,
  type IRequestParamsValue,
  type JsonSchema,
  PARAMETER_LOCATIONS,
  type ParameterLocation,
  type ScalarParameterType,
} from './types';

const STRUCTURAL_SCHEMA_KEYS = [
  'description',
  'items',
  'properties',
  'required',
  'type',
];

/** 判断输入是否为非数组的普通对象。 */
const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

/** 将普通对象收窄为组件可处理的 JSON Schema 对象。 */
const isJsonSchemaObject = (value: unknown): value is IJsonSchemaObject => {
  return isRecord(value);
};

/** 判断输入是否为请求参数支持的 header、query 或 path 位置。 */
const isParameterLocation = (value: unknown): value is ParameterLocation => {
  return PARAMETER_LOCATIONS.includes(value as ParameterLocation);
};

/** 解析 Schema 类型，并将 integer 统一映射为编辑器使用的 number。 */
const getSchemaType = (schema: IJsonSchemaObject): BodyParameterType => {
  const rawType = Array.isArray(schema.type)
    ? schema.type.find(type => type !== 'null')
    : schema.type;

  if (rawType === 'integer' || rawType === 'number') {
    return 'number';
  }

  if ([
    'array',
    'boolean',
    'object',
    'string',
  ].includes(String(rawType))) {
    return rawType as BodyParameterType;
  }

  if (isRecord(schema.properties)) {
    return 'object';
  }

  if (schema.items) {
    return 'array';
  }

  return 'string';
};

/** 提取非结构性的 Schema 配置，供字段设置浮窗继续编辑。 */
const getSchemaOptions = (schema: IJsonSchemaObject) => {
  const options = cloneDeep(schema);
  STRUCTURAL_SCHEMA_KEYS.forEach((key) => {
    delete options[key];
  });
  // 表格将 integer 展示为 number，保留原始约束供保存时还原。
  if (schema.type === 'integer') {
    options.type = 'integer';
  }
  return options;
};

/** 将未知输入规范化为可安全修改的 Schema 副本。 */
const normalizeSchema = (schema: unknown): IJsonSchemaObject => {
  if (isJsonSchemaObject(schema)) {
    return cloneDeep(schema);
  }

  return {};
};

/** 将 Schema 限制为基础类型，并移除 header、query、path 不支持的嵌套结构。 */
const normalizeScalarSchema = (schema: IJsonSchemaObject) => {
  const type = getSchemaType(schema);
  const scalarType: ScalarParameterType = [
    'string',
    'number',
    'boolean',
  ].includes(type)
    ? type as ScalarParameterType
    : 'string';
  const normalizedSchema = cloneDeep(schema);

  delete normalizedSchema.items;
  delete normalizedSchema.properties;
  delete normalizedSchema.required;
  normalizedSchema.type = schema.type === 'integer' ? 'integer' : scalarType;

  return normalizedSchema;
};

/** 创建一个带唯一标识的 Body 字段行。 */
export const createRequestField = (
  type: BodyParameterType = 'string',
  name = '',
): IRequestFieldRow => {
  return {
    description: '',
    id: uniqueId('request-field-'),
    name,
    options: {},
    required: false,
    type,
  };
};

/** 创建指定参数位置的空参数行，path 参数默认必填。 */
export const createRequestParameter = (
  location: ParameterLocation,
): IRequestParameterRow => {
  return {
    description: '',
    id: uniqueId('request-parameter-'),
    in: location,
    name: '',
    options: {},
    required: location === 'path',
    type: 'string',
  };
};

/** 创建使用 application/json 的空请求体状态。 */
export const createRequestBody = (): IRequestBodyState => {
  return {
    mediaType: 'application/json',
    required: false,
    root: createRequestField('object'),
  };
};

/** 创建不包含任何参数与请求体的初始编辑状态。 */
export const createEmptyRequestParamsState = (): IRequestParamsState => {
  return {
    parameters: {
      header: [],
      path: [],
      query: [],
    },
  };
};

/** 递归地将 JSON Schema 转换为 Body 参数树。 */
export const schemaToFieldRow = (
  schemaValue: JsonSchema | undefined,
  name = '',
  required = false,
): IRequestFieldRow => {
  const schema = typeof schemaValue === 'boolean'
    ? {}
    : normalizeSchema(schemaValue);
  const type = getSchemaType(schema);
  const row: IRequestFieldRow = {
    description: typeof schema.description === 'string' ? schema.description : '',
    id: uniqueId('request-field-'),
    name,
    options: getSchemaOptions(schema),
    required,
    type,
  };

  if (type === 'object') {
    const properties = isRecord(schema.properties) ? schema.properties : {};
    const requiredNames = new Set(Array.isArray(schema.required) ? schema.required : []);
    row.children = Object.entries(properties).map(([propertyName, propertySchema]) => {
      return schemaToFieldRow(
        propertySchema as JsonSchema,
        propertyName,
        requiredNames.has(propertyName),
      );
    });
  }
  else if (type === 'array') {
    const itemSchema = Array.isArray(schema.items)
      ? schema.items[0]
      : schema.items;
    row.children = itemSchema === undefined
      ? []
      : [schemaToFieldRow(itemSchema, '', false)];
  }

  return row;
};

/** 递归地将 Body 参数树还原为 JSON Schema。 */
export const fieldRowToSchema = (row: IRequestFieldRow): IJsonSchemaObject => {
  const schema = cloneDeep(row.options);
  schema.type = row.type === 'number' && schema.type === 'integer' ? 'integer' : row.type;

  if (row.description) {
    schema.description = row.description;
  }
  else {
    delete schema.description;
  }

  if (row.type === 'object') {
    const properties = Object.fromEntries(
      (row.children ?? [])
        .filter(child => child.name)
        .map(child => [child.name, fieldRowToSchema(child)]),
    );
    const required = (row.children ?? [])
      .filter(child => child.name && child.required)
      .map(child => child.name);
    schema.properties = properties;

    if (required.length) {
      schema.required = required;
    }
    else {
      delete schema.required;
    }

    delete schema.items;
  }
  else if (row.type === 'array') {
    schema.items = row.children?.[0]
      ? fieldRowToSchema(row.children[0])
      : { type: 'string' };
    delete schema.properties;
    delete schema.required;
  }
  else {
    delete schema.items;
    delete schema.properties;
    delete schema.required;
  }

  return schema;
};

/** 将单个 OpenAPI 参数转换为表格行，不支持的位置会被忽略。 */
const parameterToRow = (parameter: IOpenApiParameter): IRequestParameterRow | undefined => {
  if (!isParameterLocation(parameter.in)) {
    return undefined;
  }

  const legacySchema = {
    default: parameter.default,
    enum: parameter.enum,
    type: parameter.type,
  };
  const schema = normalizeScalarSchema(normalizeSchema(parameter.schema ?? legacySchema));
  const type = getSchemaType(schema) as ScalarParameterType;

  return {
    description: parameter.description
      ?? (typeof schema.description === 'string' ? schema.description : ''),
    id: uniqueId('request-parameter-'),
    in: parameter.in,
    name: parameter.name ?? '',
    options: getSchemaOptions(schema),
    required: parameter.in === 'path' ? true : Boolean(parameter.required),
    source: cloneDeep(parameter),
    type,
  };
};

/** 从 OpenAPI requestBody 中提取可编辑的 application/json 请求体状态。 */
const getRequestBodyState = (
  requestBody: IOpenApiRequestBody | undefined,
): IRequestBodyState | undefined => {
  if (!requestBody || !isRecord(requestBody.content)) {
    return undefined;
  }

  const sourceMediaType = requestBody.content['application/json']
    ? 'application/json'
    : Object.keys(requestBody.content)[0];
  const schema = requestBody.content[sourceMediaType]?.schema;

  if (!sourceMediaType || schema === undefined) {
    return undefined;
  }

  const root = schemaToFieldRow(schema);

  if (requestBody.description) {
    root.description = requestBody.description;
  }

  return {
    mediaType: 'application/json',
    required: Boolean(requestBody.required),
    root,
    source: cloneDeep(requestBody),
  };
};

/** 将 OpenAPI Operation 转换为请求参数编辑器的内部状态。 */
export const openApiSchemaToState = (
  operation: IOpenApiOperationSchema | undefined,
): IRequestParamsState => {
  const state = createEmptyRequestParamsState();

  if (!operation) {
    return state;
  }

  const parameters = Array.isArray(operation.parameters) ? operation.parameters : [];
  const legacyBodyParameter = parameters.find(parameter => parameter.in === 'body');
  parameters.forEach((parameter) => {
    const row = parameterToRow(parameter);

    if (row) {
      state.parameters[row.in].push(row);
    }
  });

  state.body = getRequestBodyState(operation.requestBody);

  if (!state.body && legacyBodyParameter?.schema) {
    state.body = {
      mediaType: 'application/json',
      required: Boolean(legacyBodyParameter.required),
      root: schemaToFieldRow(legacyBodyParameter.schema),
    };
    state.body.root.description = legacyBodyParameter.description ?? state.body.root.description;
  }

  return state;
};

/** 将基础参数表格行序列化为 OpenAPI Parameter。 */
const parameterRowToOpenApi = (row: IRequestParameterRow): IOpenApiParameter => {
  const schema = cloneDeep(row.options);
  schema.type = row.type === 'number' && schema.type === 'integer' ? 'integer' : row.type;

  return {
    ...cloneDeep(row.source),
    description: row.description,
    in: row.in,
    name: row.name,
    required: row.required || row.in === 'path',
    schema,
  };
};

/** 将请求参数编辑状态转换为组件对外输出的 OpenAPI 数据。 */
export const requestParamsStateToValue = (state: IRequestParamsState): IRequestParamsValue => {
  const parameters = PARAMETER_LOCATIONS.flatMap((location) => {
    return state.parameters[location].map(parameterRowToOpenApi);
  });
  const bodySchema = state.body ? fieldRowToSchema(state.body.root) : undefined;
  // 根行展示请求体说明时，保留独立的 Schema 说明，避免导入后相互覆盖。
  if (bodySchema && state.body?.source?.description) {
    const sourceSchema = state.body.source.content['application/json']?.schema;
    if (isJsonSchemaObject(sourceSchema) && typeof sourceSchema.description === 'string') {
      bodySchema.description = sourceSchema.description;
    }
    else {
      delete bodySchema.description;
    }
  }
  const requestBody: IOpenApiRequestBody | null = state.body
    ? {
      ...cloneDeep(state.body.source),
      content: {
        'application/json': {
          ...cloneDeep(state.body.source?.content['application/json']),
          schema: bodySchema,
        },
      },
      description: state.body.root.description,
      required: state.body.required,
    }
    : null;

  return {
    parameters,
    requestBody,
  };
};

/** 生成 JSON 编辑器需要展示的 OpenAPI 请求参数结构。 */
export const requestParamsStateToEditorJson = (state: IRequestParamsState) => {
  const value = requestParamsStateToValue(state);

  return {
    parameters: value.parameters,
    ...(value.requestBody ? { requestBody: value.requestBody } : {}),
  };
};

/** 按深度优先顺序展开 Body 参数树，并保留层级、父节点和 Schema 路径。 */
export const flattenRequestFields = (root: IRequestFieldRow): IFlatRequestFieldRow[] => {
  const result: IFlatRequestFieldRow[] = [];

  /** 递归遍历字段树并记录表格渲染所需的上下文。 */
  const visit = (
    row: IRequestFieldRow,
    depth: number,
    parent?: IRequestFieldRow,
    path = '#',
  ) => {
    result.push({
      depth,
      isArrayItem: parent?.type === 'array',
      isRoot: !parent,
      parent,
      path,
      row,
    });
    row.children?.forEach((child) => {
      const childPath = row.type === 'array'
        ? `${path}/items`
        : `${path}/properties/${child.name}`;
      visit(child, depth + 1, row, childPath);
    });
  };

  visit(root, 0);
  return result;
};

/** 切换字段类型，并清理新类型不兼容的子节点和 Schema 配置。 */
export const resetFieldForType = (
  row: IRequestFieldRow,
  type: BodyParameterType,
) => {
  const previousType = row.type;
  row.type = type;

  if (type === 'object') {
    row.children = previousType === 'object' ? row.children ?? [] : [];
  }
  else if (type === 'array') {
    row.children = previousType === 'array' ? row.children?.slice(0, 1) ?? [] : [];
  }
  else {
    delete row.children;
  }

  const nextOptions = cloneDeep(row.options);
  delete nextOptions.type;
  const incompatibleKeys: Record<BodyParameterType, string[]> = {
    array: [
      'format',
      'maxLength',
      'maximum',
      'minLength',
      'minimum',
      'multipleOf',
      'pattern',
    ],
    boolean: [
      'format',
      'maxItems',
      'maxLength',
      'maxProperties',
      'maximum',
      'minItems',
      'minLength',
      'minProperties',
      'minimum',
      'multipleOf',
      'pattern',
      'uniqueItems',
    ],
    number: [
      'format',
      'maxItems',
      'maxLength',
      'maxProperties',
      'minItems',
      'minLength',
      'minProperties',
      'pattern',
      'uniqueItems',
    ],
    object: [
      'format',
      'maxItems',
      'maxLength',
      'maximum',
      'minItems',
      'minLength',
      'minimum',
      'multipleOf',
      'pattern',
      'uniqueItems',
    ],
    string: [
      'maxItems',
      'maxProperties',
      'maximum',
      'minItems',
      'minProperties',
      'minimum',
      'multipleOf',
      'uniqueItems',
    ],
  };
  incompatibleKeys[type].forEach((key) => {
    delete nextOptions[key];
  });
  delete nextOptions.default;
  delete nextOptions.enum;
  delete nextOptions.examples;
  row.options = nextOptions;
};
