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
import toJsonSchema from 'to-json-schema';

import {
  type BodyParameterType,
  type IFlatResponseFieldRow,
  type IJsonSchemaObject,
  type IOpenApiOperationSchema,
  type IOpenApiResponse,
  type IResponseFieldRow,
  type IResponseParamsValue,
  type IResponseState,
  type JsonSchema,
} from './types';

const STRUCTURAL_SCHEMA_KEYS = [
  'description',
  'items',
  'properties',
  'required',
  'type',
];

const SCHEMA_HINT_KEYS = [
  '$ref',
  'allOf',
  'anyOf',
  'enum',
  'format',
  'items',
  'oneOf',
  'properties',
  'type',
];

const JSON_SCHEMA_TYPE_NAMES = [
  'array',
  'boolean',
  'integer',
  'null',
  'number',
  'object',
  'string',
];

/** 判断输入是否为非数组的普通对象。 */
const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

/** 判断输入是否为 JSON Schema 支持的布尔值或对象形式。 */
const isJsonSchema = (value: unknown): value is JsonSchema => {
  return typeof value === 'boolean' || isRecord(value);
};

/** 将未知输入规范化为可安全修改的 Schema 副本。 */
const normalizeSchema = (schema: unknown): IJsonSchemaObject => {
  return isRecord(schema) ? cloneDeep(schema) : {};
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
  return options;
};

/** 判断对象是否包含足以识别为 JSON Schema 的关键字。 */
const isSchemaLike = (value: unknown): value is IJsonSchemaObject => {
  if (!isRecord(value)) {
    return false;
  }

  if ('type' in value) {
    const types = Array.isArray(value.type) ? value.type : [value.type];
    const hasValidType = types.length > 0 && types.every((type) => {
      return JSON_SCHEMA_TYPE_NAMES.includes(String(type));
    });

    if (hasValidType) {
      return true;
    }
  }

  return SCHEMA_HINT_KEYS
    .filter(key => key !== 'type')
    .some(key => key in value);
};

/** 将普通 JSON 示例转换为 Schema，转换失败时回退为基础类型。 */
const sampleToSchema = (value: unknown): IJsonSchemaObject => {
  try {
    return normalizeSchema(toJsonSchema(value));
  }
  catch {
    const type = typeof value;

    return {
      type: type === 'boolean' || type === 'number' ? type : 'string',
    };
  }
};

/** 优先读取 application/json，并从响应 content 中提取 Schema。 */
const getResponseSchema = (response: IOpenApiResponse) => {
  if (!isRecord(response.content)) {
    return undefined;
  }

  const mediaType = response.content['application/json']
    ? 'application/json'
    : Object.keys(response.content)[0];
  const media = response.content[mediaType];

  return isRecord(media) && isJsonSchema(media.schema)
    ? media.schema
    : undefined;
};

/** 创建一个带唯一标识的响应字段行。 */
export const createResponseField = (
  type: BodyParameterType = 'string',
  name = '',
): IResponseFieldRow => {
  return {
    description: '',
    id: uniqueId('response-field-'),
    name,
    options: {},
    type,
  };
};

/** 创建响应状态，新建状态默认包含一个示例字段。 */
export const createResponseState = (
  code = '200',
  withExample = true,
): IResponseState => {
  const root = createResponseField('object');

  if (withExample) {
    root.children = [createResponseField('string', 'example')];
  }

  return {
    code,
    expanded: true,
    id: uniqueId('response-'),
    root,
  };
};

/** 递归地将 JSON Schema 转换为响应字段树。 */
export const schemaToResponseField = (
  schemaValue: JsonSchema | undefined,
  name = '',
): IResponseFieldRow => {
  const schema = typeof schemaValue === 'boolean'
    ? {}
    : normalizeSchema(schemaValue);
  const type = getSchemaType(schema);
  const row: IResponseFieldRow = {
    description: typeof schema.description === 'string' ? schema.description : '',
    id: uniqueId('response-field-'),
    name,
    options: getSchemaOptions(schema),
    type,
  };

  if (type === 'object') {
    const properties = isRecord(schema.properties) ? schema.properties : {};
    row.children = Object.entries(properties).map(([propertyName, propertySchema]) => {
      return schemaToResponseField(
        propertySchema as JsonSchema,
        propertyName,
      );
    });
  }
  else if (type === 'array') {
    const itemSchema = Array.isArray(schema.items)
      ? schema.items[0]
      : schema.items;
    row.children = itemSchema === undefined
      ? []
      : [schemaToResponseField(itemSchema, '')];
  }

  return row;
};

/** 递归地将响应字段树还原为 JSON Schema。 */
export const responseFieldToSchema = (row: IResponseFieldRow): IJsonSchemaObject => {
  const schema = cloneDeep(row.options);
  schema.type = row.type;

  if (row.description) {
    schema.description = row.description;
  }
  else {
    delete schema.description;
  }

  if (row.type === 'object') {
    schema.properties = Object.fromEntries(
      (row.children ?? [])
        .filter(child => child.name)
        .map(child => [child.name, responseFieldToSchema(child)]),
    );
    delete schema.items;
    delete schema.required;
  }
  else if (row.type === 'array') {
    schema.items = row.children?.[0]
      ? responseFieldToSchema(row.children[0])
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

/** 将单个 OpenAPI Response 转换为可编辑的响应状态。 */
const openApiResponseToState = (
  code: string,
  response: IOpenApiResponse,
): IResponseState => {
  const schema = getResponseSchema(response);
  const root = schemaToResponseField(schema ?? { type: 'object' });

  if (typeof response.description === 'string') {
    root.description = response.description;
  }

  return {
    code,
    expanded: true,
    id: uniqueId('response-'),
    root,
  };
};

/** 将 OpenAPI Operation 中的 responses 转换为响应编辑器状态列表。 */
export const openApiSchemaToResponses = (
  operation: IOpenApiOperationSchema | undefined,
): IResponseState[] => {
  if (!isRecord(operation?.responses)) {
    return [];
  }

  return Object.entries(operation.responses)
    .filter(([, response]) => isRecord(response))
    .map(([code, response]) => {
      return openApiResponseToState(code, response as unknown as IOpenApiResponse);
    });
};

/** 判断根字段是否包含需要输出到 content 的响应体结构。 */
const shouldIncludeContent = (root: IResponseFieldRow) => {
  return [
    'boolean',
    'number',
    'string',
  ].includes(root.type)
  || Boolean(root.children?.length);
};

/** 将单个响应编辑状态序列化为 OpenAPI Response。 */
export const responseStateToOpenApi = (
  response: IResponseState,
): IOpenApiResponse => {
  const body: IOpenApiResponse = {
    description: response.root.description,
  };

  if (shouldIncludeContent(response.root)) {
    body.content = {
      'application/json': {
        schema: responseFieldToSchema(response.root),
      },
    };
  }

  return body;
};

/** 按状态码汇总响应状态，生成组件对外输出的 responses 对象。 */
export const responseStatesToValue = (
  responses: IResponseState[],
): IResponseParamsValue => {
  return Object.fromEntries(
    responses.map(response => [
      response.code.trim(),
      responseStateToOpenApi(response),
    ]),
  );
};

/** 按深度优先顺序展开响应字段树，并保留层级、父节点和 Schema 路径。 */
export const flattenResponseFields = (
  root: IResponseFieldRow,
): IFlatResponseFieldRow[] => {
  const result: IFlatResponseFieldRow[] = [];

  /** 递归遍历字段树并记录表格渲染所需的上下文。 */
  const visit = (
    row: IResponseFieldRow,
    depth: number,
    parent?: IResponseFieldRow,
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
        ? path + '/items'
        : path + '/properties/' + child.name;
      visit(child, depth + 1, row, childPath);
    });
  };

  visit(root, 0);
  return result;
};

/** 切换字段类型，并清理新类型不兼容的子节点和 Schema 配置。 */
export const resetResponseFieldForType = (
  row: IResponseFieldRow,
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

/** 从包含 responses 的包装对象中选取当前状态码或首个可用响应。 */
const getWrappedResponse = (
  input: Record<string, unknown>,
  code: string,
) => {
  if (isRecord(input.responses)) {
    const response = input.responses[code]
      ?? Object.values(input.responses).find(isRecord);

    return isRecord(response) ? response : undefined;
  }

  return input;
};

/**
 * 将编辑器或导入文件中的 JSON 转换为响应字段树。
 * 兼容 OpenAPI 包装、单个 Response、JSON Schema 以及普通响应示例。
 */
export const responseJsonToField = (
  input: unknown,
  currentDescription = '',
  code = '',
): IResponseFieldRow => {
  if (isRecord(input) && isRecord(input.openapi_schema)) {
    return responseJsonToField(input.openapi_schema, currentDescription, code);
  }

  const wrappedInput = isRecord(input)
    && isRecord(input.schema)
    && (isRecord(input.schema.responses) || isRecord(input.schema.content))
    ? input.schema
    : input;
  const source = isRecord(wrappedInput)
    ? getWrappedResponse(wrappedInput, code)
    : undefined;
  let responseDescription: string | undefined;
  let schema: JsonSchema | undefined;

  if (source && isRecord(source.content)) {
    responseDescription = typeof source.description === 'string'
      ? source.description
      : undefined;
    schema = getResponseSchema(source as unknown as IOpenApiResponse);
  }
  else if (source && isJsonSchema(source.schema)) {
    responseDescription = typeof source.description === 'string'
      ? source.description
      : undefined;
    schema = source.schema;
  }
  else if (isSchemaLike(wrappedInput)) {
    schema = wrappedInput;
  }

  const root = schemaToResponseField(schema ?? sampleToSchema(wrappedInput));

  if (responseDescription !== undefined) {
    root.description = responseDescription;
  }
  else if (!root.description) {
    root.description = currentDescription;
  }

  return root;
};

/** 深拷贝响应状态列表，避免编辑数据与原始对象共享引用。 */
export const cloneResponseStates = (responses: IResponseState[]) => {
  return cloneDeep(responses);
};
